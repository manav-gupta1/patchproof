from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import create_engine, MetaData, Table, Column, String, DateTime

from packages.jobs.sql_lease_fence import SQLLeaseFence, LeaseLost


def make():
    e=create_engine("sqlite://")
    md=MetaData()
    jobs=Table(
        "jobs", md,
        Column("job_id", String, primary_key=True),
        Column("status", String, nullable=False),
        Column("worker_id", String),
        Column("lease_until", DateTime(timezone=True), nullable=False),
    )
    md.create_all(e)
    return e,jobs


def seed(e,j,owner="worker-a",seconds=10):
    now=datetime.now(timezone.utc)
    with e.begin() as c:
        c.execute(j.insert().values(
            job_id="job",status="running",worker_id=owner,
            lease_until=now+timedelta(seconds=seconds)
        ))
    return now


def test_owner_can_renew_before_expiry():
    e,j=make(); now=seed(e,j)
    out=SQLLeaseFence(e,j).renew("job","worker-a",now,30)
    assert out.worker_id=="worker-a"
    with e.connect() as c:
        row=c.execute(j.select()).mappings().one()
    stored = row["lease_until"]
    if stored.tzinfo is None:
        stored = stored.replace(tzinfo=timezone.utc)
    assert stored > now


def test_stale_owner_cannot_renew():
    e,j=make(); now=seed(e,j,owner="worker-b")
    with pytest.raises(LeaseLost):
        SQLLeaseFence(e,j).renew("job","worker-a",now,30)


def test_expired_lease_cannot_be_renewed():
    e,j=make(); now=seed(e,j,seconds=1)
    expired=now+timedelta(seconds=2)
    with pytest.raises(LeaseLost):
        SQLLeaseFence(e,j).renew("job","worker-a",expired,30)


def test_can_commit_requires_live_lease_and_owner():
    e,j=make(); now=seed(e,j)
    fence=SQLLeaseFence(e,j)
    assert fence.can_commit("job","worker-a",now) is True
    assert fence.can_commit("job","worker-b",now) is False
    assert fence.can_commit("job","worker-a",now+timedelta(seconds=20)) is False
