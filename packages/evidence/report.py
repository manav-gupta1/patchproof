from __future__ import annotations


class PRReportRenderer:
    def render(self, *, finding, patch, verification, environment) -> str:
        status = "VERIFIED" if verification.get("verified") else "NOT VERIFIED"
        semgrep = verification.get("semgrep_finding_count", 0)

        lines = [
            f"## PatchProof: {status}",
            "",
            "### Security finding",
            f"- Rule: `{finding.get('rule_id', 'unknown')}`",
            f"- File: `{finding.get('path', 'unknown')}`",
            f"- Severity: `{finding.get('severity', 'unknown')}`",
            "",
            "### Patch",
            f"- Changed files: {', '.join(patch.get('changed_files', []))}",
            f"- Confidence: {patch.get('confidence', 0):.2f}",
            f"- Rationale: {patch.get('security_rationale', '')}",
            "",
            "### Verification evidence",
            f"- Baseline exploit reproduced: `{verification.get('baseline_reproduced')}`",
            f"- Patched exploit blocked: `{verification.get('patched_blocked')}`",
            f"- Tests passed: `{verification.get('tests_passed')}`",
            f"- Semgrep findings remaining: `{semgrep}`",
            "",
            "### Environment",
            f"- Runtime: `{environment.get('runtime', 'unknown')}`",
            f"- Python: `{environment.get('python', 'unknown')}`",
            f"- Verification mode: `{environment.get('verification_mode', 'unknown')}`",
            "",
            "### Trust statement",
            (
                "PatchProof marks this remediation VERIFIED only when the baseline "
                "exploit reproduces, the patched exploit is blocked, tests pass, "
                "and the post-patch Semgrep scan is clean."
            ),
        ]
        return "\n".join(lines)
