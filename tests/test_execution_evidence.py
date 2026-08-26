import pytest

from packages.evidence.execution import (
    ScannerResult, TestResult, VerificationResult,
    build_execution_evidence, build_authoritative_bundle,
)


def results(verified=True):
    return (
        ScannerResult(0, "scanner: 0 findings"),
        TestResult(42, 0, "42 passed"),
        VerificationResult(verified, "verification complete"),
    )


def test_execution_outputs_become_evidence():
    scanner, tests, verification = results()
    execution = build_execution_evidence(scanner, tests, verification)
    assert execution.scanner.sha256
    assert execution.tests.sha256
    assert execution.verification.sha256
    assert len(execution.evidence_sha256) == 64


def test_authoritative_bundle_uses_actual_results():
    scanner, tests, verification = results()
    bundle, execution = build_authoritative_bundle(
        "job-1", "a" * 40, "diff", scanner, tests, verification
    )
    assert bundle.scanner_summary == "0 findings"
    assert bundle.test_summary == "42 passed, 0 failed"
    assert bundle.verification_summary == "verification passed"
    assert execution.evidence_sha256


def test_failed_verification_cannot_become_authoritative():
    scanner, tests, verification = results(False)
    with pytest.raises(ValueError):
        build_authoritative_bundle(
            "job-1", "a" * 40, "diff", scanner, tests, verification
        )


def test_changed_output_changes_execution_digest():
    scanner, tests, verification = results()
    first = build_execution_evidence(scanner, tests, verification)
    changed = build_execution_evidence(
        ScannerResult(1, "scanner: 1 finding"), tests, verification
    )
    assert first.evidence_sha256 != changed.evidence_sha256
