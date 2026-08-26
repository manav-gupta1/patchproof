from pathlib import Path
import json
import platform
import sys

from packages.evidence.bundle import EvidenceBundleBuilder
from packages.evidence.report import PRReportRenderer

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("evidence")
root.mkdir(parents=True, exist_ok=True)

builder = EvidenceBundleBuilder(root)
finding = {
    "rule_id": "python.sql-string-format",
    "path": "app.py",
    "severity": "ERROR",
    "start_line": 14,
    "end_line": 14,
}
patch = {
    "changed_files": ["app.py"],
    "confidence": 0.99,
    "security_rationale": "Prevents attacker-controlled SQL syntax.",
}
verification = {
    "baseline_reproduced": True,
    "patched_blocked": True,
    "tests_passed": True,
    "semgrep_clean": True,
    "semgrep_finding_count": 0,
    "verified": True,
}
environment = {
    "runtime": "gVisor/runsc",
    "python": platform.python_version(),
    "verification_mode": "isolated",
}

builder.add_json("finding.json", finding)
builder.add_json("verification.json", verification)
builder.add_json("environment.json", environment)

report = PRReportRenderer().render(
    finding=finding,
    patch=patch,
    verification=verification,
    environment=environment,
)
builder.add_text("pr-report.md", report, "text/markdown")

manifest = builder.manifest(
    finding=finding,
    patch=patch,
    verification=verification,
    environment=environment,
)
builder.write_manifest(manifest)
print(root / "manifest.json")
