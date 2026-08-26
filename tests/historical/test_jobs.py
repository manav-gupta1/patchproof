from types import SimpleNamespace
import pytest

from packages.jobs.state import JobState, JobStateMachine, JobRecord
from packages.jobs.store import InMemoryJobStore
from packages.jobs.service import JobService


def payload(delivery="d1"):
    return SimpleNamespace(repository="acme/demo", delivery_id=delivery)


def test_state_machine_enforces_order():
    sm = JobStateMachine()
    job = JobRecord("j1", "acme/demo", "d1", "a"*40)
    job = sm.transition(job, JobState.QUEUED)
    job = sm.transition(job, JobState.CLONING)
    assert job.state is JobState.CLONING
    with pytest.raises(ValueError):
        sm.transition(job, JobState.VERIFIED)


def test_duplicate_delivery_is_idempotent():
    service = JobService(InMemoryJobStore(), JobStateMachine())
    a = service.create_from_github(payload("same"), "a"*40)
    b = service.create_from_github(payload("same"), "a"*40)
    assert a.job_id == b.job_id


def test_failure_is_terminal():
    service = JobService(InMemoryJobStore(), JobStateMachine())
    job = service.create_from_github(payload(), "b"*40)
    failed = service.fail(job.job_id, "sandbox timeout")
    assert failed.state is JobState.FAILED
    with pytest.raises(ValueError):
        service.transition(job.job_id, JobState.VERIFIED)
