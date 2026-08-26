from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import create_engine

from packages.jobs.sql_store import SQLJobStore
from packages.jobs.worker import JobLeaseError, JobStatus


def make():
    engine=create_engine("sqlite://")
    store=SQLJobStore(engine)
    store.create_schema()
    return store


def test_succeed_requires_live_lease():
    store=make()
    job_id=store.create("live-lease")
    now=datetime.now(timezone.utc)
    assert store.claim(job_id,"worker",lease_seconds=10,now=now)

    store.succeed(job_id,"worker",now=now+timedelta(seconds=1))
    assert store.get(job_id).status == JobStatus.SUCCEEDED


def test_expired_worker_cannot_succeed():
    store=make()
    job_id=store.create("expired")
    now=datetime.now(timezone.utc)
    assert store.claim(job_id,"worker",lease_seconds=1,now=now)

    with pytest.raises(JobLeaseError):
        store.succeed(job_id,"worker",now=now+timedelta(seconds=2))

    job=store.get(job_id)
    assert job.status == JobStatus.RUNNING
    assert job.lease_owner == "worker"


def test_stale_worker_cannot_succeed_after_reclaim():
    store=make()
    job_id=store.create("reclaim")
    now=datetime.now(timezone.utc)

    assert store.claim(job_id,"old",lease_seconds=1,now=now)
    later=now+timedelta(seconds=2)
    assert store.claim(job_id,"new",lease_seconds=10,now=later)

    with pytest.raises(JobLeaseError):
        store.succeed(job_id,"old",now=later)

    store.succeed(job_id,"new",now=later)
    assert store.get(job_id).status == JobStatus.SUCCEEDED
