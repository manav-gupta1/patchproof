from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from packages.evidence.artifacts import ExecutionArtifact, ExecutionEvidence
from packages.evidence.models import EvidenceBundle


@dataclass(frozen=True)
class ScannerResult:
    findings: int
    output: str


@dataclass(frozen=True)
class TestResult:
    # Prevent pytest from mistaking this imported data class for a test class.
    __test__ = False
    passed: int
    failed: int
    output: str


@dataclass(frozen=True)
class VerificationResult:
    verified: bool
    output: str


def build_execution_evidence(scanner, tests, verification):
    if scanner.findings < 0:
        raise ValueError("scanner finding count cannot be negative")
    if tests.passed < 0 or tests.failed < 0:
        raise ValueError("test counts cannot be negative")

    evidence = ExecutionEvidence(
        scanner=ExecutionArtifact("scanner", "scanner-output", scanner.output),
        tests=ExecutionArtifact("tests", "test-output", tests.output),
        verification=ExecutionArtifact(
            "verification", "verification-output", verification.output
        ),
    )
    evidence.validate()
    return evidence


def build_authoritative_bundle(job_id, commit_sha, patch_diff, scanner, tests, verification):
    if not verification.verified:
        raise ValueError("cannot create authoritative evidence from failed verification")
    execution = build_execution_evidence(scanner, tests, verification)

    scanner_summary = f"{scanner.findings} findings"
    test_summary = f"{tests.passed} passed, {tests.failed} failed"
    verification_summary = "verification passed"

    return EvidenceBundle(
        job_id=job_id,
        commit_sha=commit_sha,
        patch_sha256=sha256(patch_diff.encode()).hexdigest(),
        scanner_summary=scanner_summary,
        test_summary=test_summary,
        verification_summary=verification_summary,
    ), execution
