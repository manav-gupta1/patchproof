from pathlib import Path
import shutil, subprocess, sys, tempfile, os
ROOT = Path(__file__).parents[1]
os.environ['PYTHONPATH'] = str(ROOT) + os.pathsep + os.environ.get('PYTHONPATH', '')
from packages.patching.fixture_patch import SQLInjectionFixturePatcher

FIXTURE = ROOT / "fixtures" / "sql_injection"

def run(repo):
    return subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=repo,
                          capture_output=True, text=True)

def main():
    with tempfile.TemporaryDirectory(prefix="patchproof-e2e-") as td:
        repo = Path(td) / "repo"
        shutil.copytree(FIXTURE, repo)
        baseline = run(repo)
        print("BASELINE:", "VULNERABLE (regression reproduced)" if baseline.returncode else "NOT REPRODUCED")
        proposal = SQLInjectionFixturePatcher().propose(
            repo, {"rule_id": "patchproof.python.sql-injection", "path": "app/db.py"})
        print("PATCH:", proposal["changed_files"])
        patched = run(repo)
        print("PATCHED:", "VERIFIED BY TESTS" if patched.returncode == 0 else "FAILED")
        if patched.returncode != 0:
            print(patched.stdout, patched.stderr)
            raise SystemExit(1)

if __name__ == "__main__":
    main()
