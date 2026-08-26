from datetime import datetime, timedelta, timezone
import pytest

from packages.jobs.worker import (
    InMemoryJobStore, JobStatus, JobWorker, JobLeaseError
)


def test_two_workers_cannot_claim_same_live_job():
    store = InMemoryJobStore()
    store.create("job-1")
    first = JobWorker(store, "worker-a")
    second = JobWorker(store, "worker-b")

    assert first.store.claim("job-1", "worker-a")
    assert second.store.claim("job-1", "worker-b") is False
    assert store.get("job-1").lease_owner == "worker-a"


def test_expired_lease_can_be_recovered():
    store = InMemoryJobStore()
    store.create("job-2")
    now = datetime.now(timezone.utc)
    assert store.claim("job-2", "worker-a", lease_seconds=1, now=now)

    later = now + timedelta(seconds=2)
    assert store.claim("job-2", "worker-b", lease_seconds=60, now=later)
    assert store.get("job-2").lease_owner == "worker-b"
    assert store.get("job-2").attempts == 2


def test_old_worker_cannot_complete_reclaimed_job():
    store = InMemoryJobStore()
    store.create("job-3")
    now = datetime.now(timezone.utc)
    store.claim("job-3", "worker-a", lease_seconds=1, now=now)
    store.claim(
        "job-3", "worker-b", lease_seconds=60,
        now=now + timedelta(seconds=2)
    )

    with pytest.raises(JobLeaseError):
        store.succeed("job-3", "worker-a")


def test_success_is_idempotently_terminal():
    store = InMemoryJobStore()
    store.create("job-4")
    worker = JobWorker(store, "worker-a")
    calls = []

    assert worker.run_once("job-4", lambda: calls.append(1))
    assert worker.run_once("job-4", lambda: calls.append(1)) is False
    assert calls == [1]
    assert store.get("job-4").status == JobStatus.SUCCEEDED


def test_failure_releases_ownership_and_records_error():
    store = InMemoryJobStore()
    store.create("job-5")
    worker = JobWorker(store, "worker-a")

    with pytest.raises(ValueError):
        worker.run_once("job-5", lambda: (_ for _ in ()).throw(ValueError("boom")))

    record = store.get("job-5")
    assert record.status == JobStatus.FAILED
    assert record.lease_owner is None
    assert record.last_error == "boom"
