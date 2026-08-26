import hashlib
import json
from pathlib import Path

from packages.evidence.bundle import EvidenceBundleBuilder
from packages.evidence.report import PRReportRenderer


def test_evidence_artifacts_are_hashed(tmp_path):
    b = EvidenceBundleBuilder(tmp_path)
    artifact = b.add_text("stdout.txt", "PASS\n")
    assert artifact.sha256 == hashlib.sha256(b"PASS\n").hexdigest()
    assert artifact.size == 5

    manifest = b.manifest(
        finding={"rule_id": "x"},
        patch={"changed_files": ["app.py"]},
        verification={"verified": True},
        environment={"runtime": "runsc"},
    )
    b.write_manifest(manifest)
    saved = json.loads((tmp_path / "manifest.json").read_text())
    assert saved["schema_version"] == "1.0"
    assert saved["artifacts"][0]["sha256"] == artifact.sha256


def test_pr_report_explains_verification_gates():
    report = PRReportRenderer().render(
        finding={"rule_id": "x", "path": "app.py", "severity": "ERROR"},
        patch={"changed_files": ["app.py"], "confidence": .9, "security_rationale": "fix"},
        verification={
            "verified": True,
            "baseline_reproduced": True,
            "patched_blocked": True,
            "tests_passed": True,
            "semgrep_finding_count": 0,
        },
        environment={"runtime": "runsc", "python": "3.13", "verification_mode": "isolated"},
    )
    assert "VERIFIED" in report
    assert "Baseline exploit reproduced: `True`" in report
    assert "Patched exploit blocked: `True`" in report
    assert "Semgrep findings remaining: `0`" in report
