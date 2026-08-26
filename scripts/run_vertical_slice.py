import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parents[1]))
from pathlib import Path
import json
import os
import tempfile
import shutil
import subprocess

from packages.ai.fixture_model import FixtureSQLInjectionModel
from packages.remediation.vertical_slice import VerticalSlice


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "fixtures" / "sql_injection"


def main():
    with tempfile.TemporaryDirectory(prefix="patchproof-vertical-") as td:
        repo = Path(td) / "repo"
        shutil.copytree(FIXTURE, repo)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", "test@patchproof.local"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "PatchProof Test"], cwd=repo, check=True)
        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "baseline"], cwd=repo, check=True)
        os.environ["PATH"] = str(ROOT / "tests" / "bin") + os.pathsep + os.environ["PATH"]

        finding = {
            "rule_id": "patchproof.python.sql-injection",
            "path": "app/db.py",
            "start_line": 4,
            "end_line": 4,
            "severity": "ERROR",
            "message": "User-controlled SQL concatenation",
        }
        bundle = VerticalSlice(FixtureSQLInjectionModel()).run(
            repo, finding, job_id="local-vertical-slice"
        )
        print(json.dumps(bundle.as_dict(), indent=2))
        print("\nRESULT: VERIFIED" if bundle.verified else "\nRESULT: FAILED")


if __name__ == "__main__":
    main()
