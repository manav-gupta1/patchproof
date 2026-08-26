from pathlib import Path

import pytest

from packages.context.repo import RepoCheckout
from packages.patching.contracts import PatchProposal
from packages.patching.parser import UnifiedDiffParser
from packages.patching.validator import PatchValidator


DIFF = """diff --git a/app.py b/app.py
index 1111111..2222222 100644
--- a/app.py
+++ b/app.py
@@ -1,3 +1,3 @@
-def lookup_user(name):
+def lookup_user(name):
     return name
"""


def proposal(diff=DIFF, files=None):
    return PatchProposal(
        diff=diff,
        changed_files=files or ["app.py"],
        explanation="Normalize the lookup path.",
        security_rationale="Removes the unsafe operation identified by the finding.",
        assumptions=[],
        confidence=0.91,
        model="test",
        provider="fake",
    )


def test_patch_contract_and_diff_parser():
    p = proposal()
    p.validate_shape()
    assert UnifiedDiffParser().changed_files(p.diff) == ["app.py"]


def test_validator_rejects_mismatched_declared_files():
    repo = RepoCheckout(Path(__file__).resolve().parents[1])
    with pytest.raises(ValueError):
        PatchValidator(repo).validate(proposal(files=["other.py"]))


def test_validator_rejects_path_escape():
    unsafe = DIFF.replace("b/app.py", "b/../secret.txt").replace("a/app.py", "a/../secret.txt")
    p = proposal(diff=unsafe, files=["../secret.txt"])
    repo = RepoCheckout(Path(__file__).resolve().parents[1])
    with pytest.raises(ValueError):
        PatchValidator(repo).validate(p)


def test_validator_rejects_invalid_confidence():
    p = proposal()
    p2 = PatchProposal(
        diff=p.diff, changed_files=p.changed_files,
        explanation=p.explanation, security_rationale=p.security_rationale,
        confidence=2,
    )
    with pytest.raises(ValueError):
        p2.validate_shape()


def test_patch_is_checked_before_application():
    repo = RepoCheckout(Path(__file__).resolve().parents[1])
    bad = proposal(diff=DIFF.replace("return name", "return definitely_missing"))
    with pytest.raises(Exception):
        PatchValidator(repo).apply(bad)
