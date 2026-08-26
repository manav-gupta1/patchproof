from __future__ import annotations

import json


def build_pr_body(
    *,
    finding: dict,
    patch: dict,
    verification: dict,
    evidence_id: str,
) -> str:
    verdict = "VERIFIED" if verification.get("verified") else "NOT VERIFIED"
    return f"""## PatchProof remediation

**Verdict:** `{verdict}`

### Finding
- Rule: `{finding.get("rule_id", "unknown")}`
- File: `{finding.get("path", "unknown")}`
- Lines: `{finding.get("start_line", "?")}-{finding.get("end_line", "?")}`
- Fingerprint: `{finding.get("fingerprint", "unknown")}`

### Patch
- Provider: `{patch.get("model_provider", "unknown")}`
- Model: `{patch.get("model_name", "unknown")}`
- Patch ID: `{patch.get("patch_id", "unknown")}`

### Verification
- Baseline exploit reproduced: `{verification.get("baseline_reproduced")}`
- Patched exploit blocked: `{verification.get("patched_blocked")}`
- Tests passed: `{verification.get("tests_passed")}`
- Semgrep clean: `{verification.get("semgrep_clean")}`
- Semgrep findings: `{verification.get("semgrep_finding_count")}`

Evidence artifact: `{evidence_id}`

> PatchProof never treats model output as verification. The verdict comes from executable evidence.
"""
