from types import SimpleNamespace
import pytest
from sqlalchemy import create_engine

from packages.evidence.store import EvidenceStore
from packages.github.fake_client import FakeGitHubClient
from packages.github.publisher import GitHubPublisher, VerifiedPublicationService, PublicationRejected
from packages.jobs.state import JobState, JobStateMachine
from packages.verification.service import DurableVerificationService
from packages.execution.pipeline import PipelineResult
from packages.evidence.execution import ScannerResult, TestResult, VerificationResult, build_execution_evidence


def setup_verified():
    engine = create_engine("sqlite://")
    evidence = EvidenceStore(engine)
    evidence.create_schema()
    machine = JobStateMachine()
    job = SimpleNamespace(job_id="job-pr-1", commit_sha="a" * 40)
    machine.create(job.job_id)
    machine.mark_scanning(job.job_id)
    machine.mark_verifying(job.job_id)

    class Pipeline:
        def run(self):
            scanner = ScannerResult(0, "scanner clean")
            tests = TestResult(24, 0, "24 passed")
            verification = VerificationResult(True, "verified")
            execution = build_execution_evidence(scanner, tests, verification)
            return PipelineResult(scanner, tests, verification, execution)

    bundle, _ = DurableVerificationService(Pipeline(), evidence, machine).verify(
        job=job, patch_diff="diff"
    )
    return job, machine, evidence, bundle


def test_only_verified_job_can_publish():
    job, machine, evidence, bundle = setup_verified()
    client = FakeGitHubClient()
    service = VerifiedPublicationService(machine, evidence, GitHubPublisher(client))
    pr = service.publish(
        job=job, title="PatchProof remediation", body="Evidence-backed remediation",
        head="patchproof/job-pr-1", base="main",
    )
    assert machine.state(job.job_id) == JobState.PR_CREATED
    assert pr["number"] == 1
    assert client.create_calls == 1


def test_publish_is_idempotent_for_same_evidence():
    job, machine, evidence, bundle = setup_verified()
    client = FakeGitHubClient()
    service = VerifiedPublicationService(machine, evidence, GitHubPublisher(client))
    kwargs = dict(
        job=job, title="PatchProof remediation", body="Evidence-backed remediation",
        head="patchproof/job-pr-1", base="main",
    )
    first = service.publish(**kwargs)
    machine._states[job.job_id] = JobState.VERIFIED
    second = service.publish(**kwargs)
    assert first == second
    assert client.create_calls == 1


def test_queued_job_cannot_publish():
    engine = create_engine("sqlite://")
    evidence = EvidenceStore(engine)
    evidence.create_schema()
    machine = JobStateMachine()
    job = SimpleNamespace(job_id="queued-pr", commit_sha="b" * 40)
    machine.create(job.job_id)
    service = VerifiedPublicationService(machine, evidence, GitHubPublisher(FakeGitHubClient()))
    with pytest.raises(PublicationRejected):
        service.publish(job=job, title="x", body="x", head="patchproof/queued-pr", base="main")
