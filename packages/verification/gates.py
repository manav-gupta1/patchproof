from __future__ import annotations

from packages.verification.models import SemgrepResult, VerificationReport
from packages.verification.tests import TestRun


def build_report(
    *,
    baseline_exploit_reproduced: bool,
    patched_exploit_blocked: bool,
    tests: TestRun,
    semgrep_after: SemgrepResult,
    original_fingerprint: str,
) -> VerificationReport:
    remaining_original = [
        f for f in semgrep_after.findings
        if f.fingerprint == original_fingerprint
    ]

    semgrep_clean = len(remaining_original) == 0
    verified = (
        baseline_exploit_reproduced
        and patched_exploit_blocked
        and tests.passed
        and semgrep_clean
    )

    notes = []
    if not baseline_exploit_reproduced:
        notes.append("baseline exploit did not reproduce")
    if not patched_exploit_blocked:
        notes.append("patched exploit still succeeds")
    if not tests.passed:
        notes.append("repository tests failed")
    if not semgrep_clean:
        notes.append("original Semgrep finding remains")

    return VerificationReport(
        baseline_exploit_reproduced=baseline_exploit_reproduced,
        patched_exploit_blocked=patched_exploit_blocked,
        tests_passed=tests.passed,
        semgrep_clean=semgrep_clean,
        semgrep_finding_count=len(semgrep_after.findings),
        verified=verified,
        notes=notes,
    )
