from types import SimpleNamespace
from sqlalchemy import create_engine

from packages.jobs.sql_store import SQLJobStore
from packages.jobs.pipeline_worker import EndToEndWorker


class Verification:
    def __init__(self):
        self.calls = 0

    def verify(self, *, job, patch_diff):
        self.calls += 1
        return "evidence-bundle", None


class Publication:
    def __init__(self):
        self.calls = 0

    def publish(self, **kwargs):
        self.calls += 1
        return {"number": 1, "url": "https://github.example/pr/1"}


def make():
    engine = create_engine("sqlite://")
    store = SQLJobStore(engine)
    store.create_schema()
    job = SimpleNamespace(job_id="job-e2e")
    store.create(job.job_id)
    verification = Verification()
    publication = Publication()
    worker = EndToEndWorker(store, verification, publication)
    return store, job, verification, publication, worker


def test_full_worker_path_is_lease_owned():
    store, job, verification, publication, worker = make()

    assert worker.run(
        job=job, patch_diff="diff",
        title="PatchProof", body="Evidence", 
        head="patchproof/job-e2e", base="main",
        worker_id="worker-a",
    )

    assert verification.calls == 1
    assert publication.calls == 1
    assert store.get(job.job_id).status.value == "succeeded"
    assert store.get(job.job_id).lease_owner is None


def test_second_worker_cannot_execute_same_job():
    store, job, verification, publication, worker = make()
    assert store.claim(job.job_id, "worker-a")
    assert worker.run(
        job=job, patch_diff="diff",
        title="PatchProof", body="Evidence",
        head="patchproof/job-e2e", base="main",
        worker_id="worker-b",
    ) is False
    assert verification.calls == 0
    assert publication.calls == 0


def test_failure_is_recorded_and_ownership_released():
    store, job, verification, publication, worker = make()

    def fail(**kwargs):
        raise RuntimeError("publication unavailable")

    worker.publication_service.publish = fail

    try:
        worker.run(
            job=job, patch_diff="diff",
            title="PatchProof", body="Evidence",
            head="patchproof/job-e2e", base="main",
            worker_id="worker-a",
        )
        assert False
    except RuntimeError:
        pass

    record = store.get(job.job_id)
    assert record.status.value == "failed"
    assert record.lease_owner is None
    assert "publication unavailable" in record.last_error
