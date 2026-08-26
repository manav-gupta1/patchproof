import time
import pytest

from packages.durable.store import DurableJobStore
from packages.durable.queue import JobQueue


def test_job_and_transition_are_durable_and_audited():
    store = DurableJobStore()
    store.create("j1")
    store.transition("j1", "RECEIVED", "CONTEXT_READY", attempt=1)
    assert store.get("j1")[1] == "CONTEXT_READY"
    events = store.events("j1")
    assert events == [("j1", "RECEIVED", "CONTEXT_READY", 1, None)]


def test_stale_transition_is_rejected():
    store = DurableJobStore()
    store.create("j2")
    store.transition("j2", "RECEIVED", "CONTEXT_READY")
    with pytest.raises(ValueError):
        store.transition("j2", "RECEIVED", "PATCH_PROPOSED")


def test_lease_prevents_two_workers_running_same_job():
    store = DurableJobStore()
    store.create("j3")
    assert store.acquire_lease("j3", "worker-a", 100.0, 30)
    assert not store.acquire_lease("j3", "worker-b", 110.0, 30)
    store.release_lease("j3", "worker-a")
    assert store.acquire_lease("j3", "worker-b", 110.0, 30)


def test_expired_lease_can_be_recovered():
    store = DurableJobStore()
    store.create("j4")
    assert store.acquire_lease("j4", "worker-a", 100.0, 5)
    assert store.acquire_lease("j4", "worker-b", 106.0, 30)


def test_queue_round_trip():
    q = JobQueue()
    q.enqueue("j5")
    lease = q.claim("worker-a")
    assert lease.job_id == "j5"
    assert lease.owner == "worker-a"
