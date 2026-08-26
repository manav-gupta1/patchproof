import pytest
from sqlalchemy import create_engine, text

from packages.jobs.sql_result_fence import SQLResultFence, StaleResultRejected


def make():
    engine = create_engine("sqlite://")
    engine.execute if hasattr(engine, "execute") else None
    from sqlalchemy import MetaData, Table, Column, String, JSON
    md=MetaData()
    jobs=Table(
        "jobs", md,
        Column("job_id", String, primary_key=True),
        Column("status", String, nullable=False),
        Column("worker_id", String),
        Column("result", JSON),
    )
    md.create_all(engine)
    return engine,jobs


def seed(engine,jobs,worker="old"):
    with engine.begin() as c:
        c.execute(jobs.insert().values(
            job_id="job", status="running", worker_id=worker, result=None
        ))


def test_current_owner_can_commit_atomically():
    e,j=make(); seed(e,j,"new")
    out=SQLResultFence(e,j).commit("job","new",{"value":"authoritative"})
    assert out.job_id=="job"
    with e.connect() as c:
        row=c.execute(j.select()).mappings().one()
    assert row["status"]=="succeeded"
    assert row["worker_id"] is None
    assert row["result"]=={"value":"authoritative"}


def test_stale_owner_cannot_commit():
    e,j=make(); seed(e,j,"new")
    with pytest.raises(StaleResultRejected):
        SQLResultFence(e,j).commit("job","old",{"value":"stale"})
    with e.connect() as c:
        row=c.execute(j.select()).mappings().one()
    assert row["status"]=="running"
    assert row["worker_id"]=="new"
    assert row["result"] is None


def test_result_fence_is_single_use():
    e,j=make(); seed(e,j,"new")
    fence=SQLResultFence(e,j)
    fence.commit("job","new",{"value":"first"})
    with pytest.raises(StaleResultRejected):
        fence.commit("job","new",{"value":"second"})
    with e.connect() as c:
        row=c.execute(j.select()).mappings().one()
    assert row["result"]=={"value":"first"}
