import shutil
from pathlib import Path

from packages.ai.fixture_model import FixtureSQLInjectionModel
from packages.evidence.bundle import EvidenceBuilder
from packages.remediation.vertical_slice import VerticalSlice


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "fixtures" / "sql_injection"


def test_full_vertical_slice_produces_verified_evidence(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    shutil.copytree(FIXTURE, repo)
    # The patch boundary intentionally uses git apply/reset. The fixture is
    # source-only, so create a disposable repository around it for the E2E.
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "-c", "user.name=PatchProof", "-c", "user.email=patchproof@test", "commit", "-qm", "fixture"], cwd=repo, check=True)

    # Put our deterministic Semgrep stand-in first on PATH.
    monkeypatch.setenv("PATH", str(ROOT / "tests" / "bin") + ":" + __import__("os").environ["PATH"])

    finding = {
        "rule_id": "patchproof.python.sql-injection",
        "path": "app/db.py",
        "start_line": 4,
        "end_line": 4,
        "severity": "ERROR",
        "message": "User-controlled SQL concatenation",
    }

    monkeypatch.setenv("PATCHPROOF_ALLOW_LOCAL_SANDBOX", "1")
    bundle = VerticalSlice(
        FixtureSQLInjectionModel(),
        runner_factory=lambda r: __import__("packages.sandbox.runner", fromlist=["SandboxRunner"]).SandboxRunner(
            r, runtime="local"
        ),
    ).run(repo, finding, job_id="e2e-sql-1")

    assert bundle.verified is True
    assert bundle.baseline["exploit_reproduced"] is True
    assert bundle.patched["exploit_reproduced"] is False
    assert bundle.tests["passed"] is True
    assert bundle.semgrep["finding_count"] == 0
    assert bundle.patch["changed_files"] == ["app/db.py"]
    assert bundle.job_id == "e2e-sql-1"
