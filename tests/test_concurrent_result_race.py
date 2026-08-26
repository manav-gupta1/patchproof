import threading
from sqlalchemy import create_engine, MetaData, Table, Column, String, JSON

from packages.jobs.sql_result_fence import SQLResultFence, StaleResultRejected


def make():
    # SQLite shared in-memory DB lets both threads execute against the same
    # database while preserving the single conditional UPDATE invariant.
    engine=create_engine(
        "sqlite:///file:result_race?mode=memory&cache=shared&uri=true",
        connect_args={"check_same_thread": False},
    )
    md=MetaData()
    jobs=Table(
        "jobs", md,
        Column("job_id", String, primary_key=True),
        Column("status", String, nullable=False),
        Column("worker_id", String),
        Column("result", JSON),
    )
    md.create_all(engine)
    with engine.begin() as c:
        c.execute(jobs.insert().values(
            job_id="race", status="running", worker_id="worker-a", result=None
        ))
    return engine, jobs


def test_two_workers_racing_to_commit_only_one_wins():
    engine,jobs=make()
    fence=SQLResultFence(engine,jobs)
    barrier=threading.Barrier(2)
    results=[]
    lock=threading.Lock()

    def attempt(worker, value):
        barrier.wait()
        try:
            fence.commit("race",worker,{"value":value})
            outcome=("success",worker)
        except StaleResultRejected:
            outcome=("stale",worker)
        with lock:
            results.append(outcome)

    a=threading.Thread(target=attempt,args=("worker-a","A"))
    b=threading.Thread(target=attempt,args=("worker-a","B"))
    a.start(); b.start(); a.join(); b.join()

    assert sum(x[0]=="success" for x in results)==1
    assert sum(x[0]=="stale" for x in results)==1

    with engine.connect() as c:
        row=c.execute(jobs.select()).mappings().one()
    assert row["status"]=="succeeded"
    assert row["result"]["value"] in {"A","B"}


def test_stale_worker_cannot_replace_authoritative_result_under_race():
    engine,jobs=make()
    fence=SQLResultFence(engine,jobs)
    fence.commit("race","worker-a",{"value":"first"})

    barrier=threading.Barrier(2)
    outcomes=[]
    lock=threading.Lock()

    def attempt(value):
        barrier.wait()
        try:
            fence.commit("race","worker-a",{"value":value})
            outcome="success"
        except StaleResultRejected:
            outcome="stale"
        with lock:
            outcomes.append(outcome)

    threads=[threading.Thread(target=attempt,args=(v,)) for v in ("second","third")]
    for t in threads: t.start()
    for t in threads: t.join()

    assert outcomes==["stale","stale"] or outcomes==["stale","stale"]
    with engine.connect() as c:
        row=c.execute(jobs.select()).mappings().one()
    assert row["result"]["value"]=="first"
