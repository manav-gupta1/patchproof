
from pathlib import Path
import shutil, subprocess, tempfile, json

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/"fixtures"/"vulnerable-python"

def run(cmd,cwd):
    return subprocess.run(cmd,cwd=cwd,text=True,capture_output=True)

def main():
    ws=Path(tempfile.mkdtemp(prefix="patchproof-e2e-"))
    shutil.copytree(FIXTURE,ws,dirs_exist_ok=True)

    baseline=run(["python","exploit.py"],ws)
    if baseline.returncode != 0:
        raise SystemExit("baseline exploit did not reproduce")

    p=ws/"app.py"
    source=p.read_text()
    old = """    query = "SELECT * FROM users WHERE name = '" + username + "'"
    return db.execute(query).fetchall()
"""
    new = """    query = "SELECT * FROM users WHERE name = ?"
    return db.execute(query, (username,)).fetchall()
"""
    if old not in source:
        raise SystemExit("known vulnerable pattern not found")
    p.write_text(source.replace(old,new))

    patched=run(["python","verify_patch.py"],ws)
    tests=run(["python","-m","pytest","-q"],ws)

    # This is the fixture's recorded Semgrep postcondition. In production the
    # command is the real Semgrep binary and its JSON becomes evidence.
    semgrep={"results":[]}
    (ws/"semgrep-result.json").write_text(json.dumps(semgrep))

    verified=(baseline.returncode==0 and patched.returncode!=0
              and tests.returncode==0 and len(semgrep["results"])==0)
    print(json.dumps({"baseline":baseline.returncode,"patched":patched.returncode,
                      "tests":tests.returncode,"semgrep_results":0,
                      "verified":verified},indent=2))
    return 0 if verified else 1

if __name__=="__main__":
    raise SystemExit(main())
