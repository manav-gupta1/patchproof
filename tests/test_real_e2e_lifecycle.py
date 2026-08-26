from pathlib import Path
import shutil
import subprocess

from packages.context.extractor import ContextExtractor
from packages.context.repo import RepoCheckout
from packages.patching.contracts import PatchProposal
from packages.patching.validator import PatchValidator
from packages.verification.engine import VerificationEngine
from packages.verification.semgrep_local import LocalSemgrepFixtureRunner
from packages.verification.executor import CommandExecutor


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "real-python-sql"

DIFF = """diff --git a/app.py b/app.py
index 1111111..2222222 100644
--- a/app.py
+++ b/app.py
@@ -12,3 +12,3 @@
 def lookup_user(conn, name):
-    query = "select role from users where name = '%s'" % name
-    return conn.execute(query).fetchone()
+    query = "select role from users where name = ?"
+    return conn.execute(query, (name,)).fetchone()
"""


def test_real_exploit_before_and_after(tmp_path):
    repo_path = tmp_path / "repo"
    shutil.copytree(FIXTURE, repo_path)
    repo = RepoCheckout(repo_path)

    finding = {
        "rule_id": "python.sql-string-format",
        "fingerprint": "fixture-sql-1",
        "path": "app.py",
        "start_line": 14,
        "end_line": 14,
        "severity": "ERROR",
    }
    context = ContextExtractor(repo).extract(finding)
    assert "execute" in context.code

    before = subprocess.run(
        ["python", "exploit.py"], cwd=repo_path, text=True,
        capture_output=True, check=False
    )
    assert before.returncode == 0
    assert "VULNERABLE" in before.stdout

    proposal = PatchProposal(
        diff=DIFF,
        changed_files=["app.py"],
        explanation="Use a parameterized SQL query.",
        security_rationale="Prevents attacker-controlled SQL syntax.",
        confidence=0.99,
    )
    PatchValidator(repo).apply(proposal)

    after = subprocess.run(
        ["python", "exploit.py"], cwd=repo_path, text=True,
        capture_output=True, check=False
    )
    assert after.returncode != 0
    assert "BLOCKED" in after.stdout

    tests = subprocess.run(
        ["python", "-m", "pytest", "-q"], cwd=repo_path,
        text=True, capture_output=True, check=False
    )
    assert tests.returncode == 0

    semgrep = LocalSemgrepFixtureRunner(repo_path).run(["."])
    assert semgrep["clean"]

    assert before.returncode == 0
    assert after.returncode != 0
    assert tests.returncode == 0
    assert semgrep["clean"]
