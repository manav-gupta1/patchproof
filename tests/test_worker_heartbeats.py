
import time
from types import SimpleNamespace
import pytest
from sqlalchemy import create_engine

from packages.jobs.pipeline_worker import EndToEndWorker, LeaseLost
from packages.jobs.sql_store import SQLJobStore


class Verification:
    def __init__(self, delay=0):
        self.delay = delay
        self.calls = 0
    def verify(self, *, job, patch_diff):
        self.calls += 1
        if self.delay:
            time.sleep(self.delay)
        return "evidence", None


class Publication:
    def __init__(self, delay=0):
        self.delay = delay
        self.calls = 0
    def publish(self, **kwargs):
        self.calls += 1
        if self.delay:
            time.sleep(self.delay)
        return {"number": 1, "url": "u"}


import tempfile
from sqlalchemy.pool import NullPool


def make():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    engine = create_engine(
        f"sqlite:///{tmp.name}",
        connect_args={"check_same_thread": False, "timeout": 30},
        poolclass=NullPool,
    )
    store = SQLJobStore(engine)
    store.create_schema()
    job = SimpleNamespace(job_id="long-job")
    store.create(job.job_id)
    return store, job


def test_long_verification_keeps_lease_alive():
    store, job = make()
    worker = EndToEndWorker(
        store, Verification(delay=0.05), Publication(),
        lease_seconds=1.0, heartbeat_interval=0.05,
    )
    assert worker.run(
        job=job, patch_diff="d", title="t", body="b",
        head="h", base="main", worker_id="w1"
    )
    assert store.get(job.job_id).status.value == "succeeded"


def test_long_publication_keeps_lease_alive():
    store, job = make()
    publication = Publication(delay=0.05)
    worker = EndToEndWorker(
        store, Verification(), publication,
        lease_seconds=1.0, heartbeat_interval=0.05,
    )
    assert worker.run(
        job=job, patch_diff="d", title="t", body="b",
        head="h", base="main", worker_id="w1"
    )
    assert publication.calls == 1


def test_heartbeat_failure_fences_worker():
    store, job = make()

    class LostStore:
        def __init__(self, wrapped):
            self.wrapped = wrapped
            self.count = 0
        def claim(self, *a, **k):
            return self.wrapped.claim(*a, **k)
        def heartbeat(self, *a, **k):
            self.count += 1
            raise RuntimeError("lease backend unavailable")
        def succeed(self, *a, **k):
            return self.wrapped.succeed(*a, **k)
        def fail(self, *a, **k):
            return self.wrapped.fail(*a, **k)

    lost = LostStore(store)
    worker = EndToEndWorker(
        lost, Verification(delay=0.08), Publication(),
        lease_seconds=0.50, heartbeat_interval=0.02,
    )
    with pytest.raises(LeaseLost):
        worker.run(
            job=job, patch_diff="d", title="t", body="b",
            head="h", base="main", worker_id="w1"
        )
    assert lost.count >= 1


def test_invalid_heartbeat_configuration_rejected():
    store, _ = make()
    with pytest.raises(ValueError):
        EndToEndWorker(
            store, Verification(), Publication(),
            lease_seconds=10, heartbeat_interval=10,
        )
