from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import create_engine, MetaData, Table, Column, String, DateTime, JSON

from packages.jobs.sql_completion import SQLCompletion, CompletionRejected


def make():
    e=create_engine("sqlite://")
    md=MetaData()
    jobs=Table(
        "jobs", md,
        Column("job_id", String, primary_key=True),
        Column("status", String, nullable=False),
        Column("worker_id", String),
        Column("lease_until", DateTime(timezone=True), nullable=False),
        Column("result", JSON),
    )
    md.create_all(e)
    return e,jobs


def seed(e,j,owner="worker-a",seconds=10):
    now=datetime.now(timezone.utc)
    with e.begin() as c:
        c.execute(j.insert().values(
            job_id="job", status="running", worker_id=owner,
            lease_until=now+timedelta(seconds=seconds), result=None
        ))
    return now


def row(e,j):
    with e.connect() as c:
        return c.execute(j.select()).mappings().one()


def test_completion_atomically_checks_owner_and_live_lease():
    e,j=make(); now=seed(e,j)
    out=SQLCompletion(e,j).commit("job","worker-a",now,{"ok":True})
    assert out.job_id=="job"
    r=row(e,j)
    assert r["status"]=="succeeded"
    assert r["worker_id"] is None
    assert r["result"]=={"ok":True}


def test_stale_worker_cannot_complete():
    e,j=make(); now=seed(e,j,owner="worker-b")
    with pytest.raises(CompletionRejected):
        SQLCompletion(e,j).commit("job","worker-a",now,{"stale":True})
    assert row(e,j)["status"]=="running"


def test_expired_worker_cannot_complete():
    e,j=make(); now=seed(e,j,seconds=1)
    expired=now+timedelta(seconds=2)
    with pytest.raises(CompletionRejected):
        SQLCompletion(e,j).commit("job","worker-a",expired,{"late":True})
    assert row(e,j)["status"]=="running"


def test_completed_job_cannot_be_completed_again():
    e,j=make(); now=seed(e,j)
    fence=SQLCompletion(e,j)
    fence.commit("job","worker-a",now,{"first":True})
    with pytest.raises(CompletionRejected):
        fence.commit("job","worker-a",now,{"second":True})
    assert row(e,j)["result"]=={"first":True}
