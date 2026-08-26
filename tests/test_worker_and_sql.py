from datetime import datetime, timezone

import pytest

from packages.orchestration.remediation import InMemoryEvidenceSink, RemediationOrchestrator
from packages.patching import DeterministicPatchModel, PatchCandidate, PatchDecision, PatchEngine
from packages.persistence.models import JobState, RemediationJob
from packages.persistence.sql import SqlJobRepository
from packages.queue.memory import MemoryQueue
from packages.queue.models import RemediationTask
from packages.worker import Worker
from packages.verification import VerificationPlan, VerificationReport


class FakeVerification:
    def run(self, workspace, plan):
        return VerificationReport(
            baseline_exploit_reproduced=True,
            patched_exploit_blocked=True,
            tests_passed=True,
            semgrep_clean=True,
            semgrep_finding_count=0,
            verified=True,
        )


def make_job():
    return RemediationJob(
        id="job-worker",
        state=JobState.RECEIVED,
        repository="acme/app",
        commit_sha="abc",
        finding_fingerprint="fp",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def make_task():
    return RemediationTask(
        job_id="job-worker",
        repository="acme/app",
        commit_sha="abc",
        finding_fingerprint="fp",
        rule_id="python.test",
        path="app.py",
        start_line=1,
        end_line=1,
        severity="high",
    )


@pytest.mark.asyncio
async def test_worker_consumes_task(tmp_path):
    target = tmp_path / "app.py"
    target.write_text("print('old')\n")

    queue = MemoryQueue()
    queue.enqueue(make_task())

    from packages.persistence.memory import MemoryJobRepository
    jobs = MemoryJobRepository()
    jobs.create(make_job())

    candidate = PatchCandidate(
        decision=PatchDecision.PATCH,
        explanation="safe",
        files={"app.py": "print('new')\n"},
        changed_files=["app.py"],
        model_provider="test",
        model_name="test",
        patch_id="p-worker",
    )

    orchestrator = RemediationOrchestrator(
        patch_engine=PatchEngine(DeterministicPatchModel(candidate)),
        verification_runner=FakeVerification(),
        state_store=jobs,
        evidence_sink=InMemoryEvidenceSink(),
    )

    worker = Worker(queue=queue, jobs=jobs, orchestrator=orchestrator)
    assert await worker.process_one(workspace=str(tmp_path))
    assert target.read_text() == "print('new')\n"
    assert jobs.get("job-worker").state is JobState.VERIFIED


def test_sql_repository_round_trip(tmp_path):
    db = SqlJobRepository(f"sqlite:///{tmp_path}/jobs.db")
    db.create_schema()

    job = make_job()
    db.create(job)

    stored = db.get(job.id)
    assert stored is not None
    assert stored.repository == "acme/app"

    db.transition(job.id, JobState.ANALYZING)
    assert db.get(job.id).state is JobState.ANALYZING
