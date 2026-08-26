
from pathlib import Path
import json

from packages.context.extractor import ContextExtractor
from packages.context.repo import RepoCheckout
from packages.patching.contracts import PatchProposal
from packages.patching.validator import PatchValidator

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "real-python-sql"

def test_real_fixture_artifact_exists():
    payload=json.loads((FIXTURE/"semgrep-result.json").read_text())
    assert isinstance(payload, dict)

def test_real_finding_context_and_patch_contract():
    repo=RepoCheckout(FIXTURE)
    finding={"rule_id":"python.sql-string-format","fingerprint":"fixture-sql-1",
             "path":"app.py","start_line":14,"end_line":14,"severity":"ERROR"}
    context=ContextExtractor(repo).extract(finding, context_lines=5)
    assert "execute" in context.code
    assert any("sqlite3" in x for x in context.imports)

    diff="""diff --git a/app.py b/app.py
index 1111111..2222222 100644
--- a/app.py
+++ b/app.py
@@ -12,3 +12,3 @@
 def lookup_user(conn, name):
-    query = "select role from users where name = '%s'" % name
+    query = "select role from users where name = ?"
-    return conn.execute(query).fetchone()
+    return conn.execute(query, (name,)).fetchone()
"""
    proposal=PatchProposal(
        diff=diff, changed_files=["app.py"],
        explanation="Use a parameterized SQL query.",
        security_rationale="Prevents user-controlled input from becoming SQL syntax.",
        confidence=0.99)
    PatchValidator(repo).validate(proposal)
