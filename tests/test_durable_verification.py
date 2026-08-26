from types import SimpleNamespace
import pytest
from sqlalchemy import create_engine

from packages.evidence.store import EvidenceStore
from packages.jobs.state import JobState, JobStateMachine
from packages.verification.service import DurableVerificationService, VerificationRejected
from packages.execution.pipeline import PipelineResult
from packages.evidence.execution import (
    ScannerResult, TestResult, VerificationResult, build_execution_evidence
)


def job():
    return SimpleNamespace(job_id="job-verify-1", commit_sha="a" * 40)


class FakePipeline:
    def __init__(self, verified=True):
        self.verified = verified

    def run(self):
        scanner = ScannerResult(0 if self.verified else 1, "scanner output")
        tests = TestResult(42 if self.verified else 0, 0 if self.verified else 1, "test output")
        verification = VerificationResult(self.verified, "verification output")
        execution = build_execution_evidence(scanner, tests, verification)
        return PipelineResult(scanner, tests, verification, execution)


def make_service(verified=True):
    engine = create_engine("sqlite://")
    evidence = EvidenceStore(engine)
    evidence.create_schema()
    machine = JobStateMachine()
    j = job()
    machine.create(j.job_id)
    machine.mark_scanning(j.job_id)
    machine.mark_analyzing(j.job_id)
    machine.mark_patching(j.job_id)
    machine.mark_verifying(j.job_id)
    return DurableVerificationService(FakePipeline(verified), evidence, machine), machine, evidence, j


def test_only_real_success_reaches_verified():
    svc, machine, evidence, j = make_service(True)
    bundle, execution = svc.verify(job=j, patch_diff="diff")
    assert machine.state(j.job_id) == JobState.VERIFIED
    assert evidence.get(j.job_id).evidence_sha256 == bundle.evidence_sha256
    assert execution.evidence_sha256


def test_failed_sandbox_verification_reaches_failed_not_verified():
    svc, machine, evidence, j = make_service(False)
    with pytest.raises(VerificationRejected):
        svc.verify(job=j, patch_diff="diff")
    assert machine.state(j.job_id) == JobState.FAILED
    assert evidence.get(j.job_id) is None


def test_verification_cannot_start_from_queued():
    engine = create_engine("sqlite://")
    evidence = EvidenceStore(engine)
    evidence.create_schema()
    machine = JobStateMachine()
    j = job()
    machine.create(j.job_id)
    with pytest.raises(VerificationRejected):
        DurableVerificationService(FakePipeline(True), evidence, machine).verify(
            job=j, patch_diff="diff"
        )
