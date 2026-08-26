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


def test_fail_requires_live_lease():
    store=make()
    job_id=store.create("live-fail")
    now=datetime.now(timezone.utc)
    assert store.claim(job_id,"worker",lease_seconds=10,now=now)

    store.fail(job_id,"worker","boom",now=now+timedelta(seconds=1))
    job=store.get(job_id)
    assert job.status == JobStatus.FAILED
    assert job.last_error == "boom"


def test_expired_worker_cannot_fail():
    store=make()
    job_id=store.create("expired-fail")
    now=datetime.now(timezone.utc)
    assert store.claim(job_id,"worker",lease_seconds=1,now=now)

    with pytest.raises(JobLeaseError):
        store.fail(job_id,"worker","late",now=now+timedelta(seconds=2))

    assert store.get(job_id).status == JobStatus.RUNNING


def test_stale_worker_cannot_fail_after_reclaim():
    store=make()
    job_id=store.create("reclaim-fail")
    now=datetime.now(timezone.utc)

    assert store.claim(job_id,"old",lease_seconds=1,now=now)
    later=now+timedelta(seconds=2)
    assert store.claim(job_id,"new",lease_seconds=10,now=later)

    with pytest.raises(JobLeaseError):
        store.fail(job_id,"old","stale",now=later)

    store.fail(job_id,"new","authoritative",now=later)
    job=store.get(job_id)
    assert job.status == JobStatus.FAILED
    assert job.last_error == "authoritative"
