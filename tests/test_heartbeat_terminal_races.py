from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import threading
import pytest
from sqlalchemy import create_engine
from packages.jobs.sql_store import SQLJobStore
from packages.jobs.worker import JobLeaseError, JobStatus

def make():
    path = Path(tempfile.mkstemp(suffix=".sqlite")[1])
    engine = create_engine(f"sqlite:///{path}")
    store = SQLJobStore(engine)
    store.create_schema()
    return store

def test_heartbeat_after_success_is_rejected():
    store=make(); job_id=store.create("hb-success")
    now=datetime.now(timezone.utc)
    assert store.claim(job_id,"worker",10,now)
    store.succeed(job_id,"worker",now+timedelta(seconds=1))
    with pytest.raises(JobLeaseError):
        store.heartbeat(job_id,"worker",10,now+timedelta(seconds=2))
    assert store.get(job_id).status == JobStatus.SUCCEEDED

def test_heartbeat_after_failure_is_rejected():
    store=make(); job_id=store.create("hb-failure")
    now=datetime.now(timezone.utc)
    assert store.claim(job_id,"worker",10,now)
    store.fail(job_id,"worker","boom",now+timedelta(seconds=1))
    with pytest.raises(JobLeaseError):
        store.heartbeat(job_id,"worker",10,now+timedelta(seconds=2))
    assert store.get(job_id).status == JobStatus.FAILED

def test_heartbeat_loses_race_to_success():
    store=make(); job_id=store.create("hb-race-success")
    now=datetime.now(timezone.utc); assert store.claim(job_id,"worker",10,now)
    barrier=threading.Barrier(2); outcomes=[]; lock=threading.Lock()
    def hb():
        barrier.wait()
        try: store.heartbeat(job_id,"worker",10,now+timedelta(seconds=1)); out="heartbeat"
        except JobLeaseError: out="rejected"
        with lock: outcomes.append(out)
    def ok():
        barrier.wait()
        try: store.succeed(job_id,"worker",now+timedelta(seconds=1)); out="success"
        except JobLeaseError: out="rejected"
        with lock: outcomes.append(out)
    ts=[threading.Thread(target=hb),threading.Thread(target=ok)]
    [t.start() for t in ts]; [t.join() for t in ts]
    assert "success" in outcomes
    assert store.get(job_id).status == JobStatus.SUCCEEDED

def test_heartbeat_loses_race_to_failure():
    store=make(); job_id=store.create("hb-race-failure")
    now=datetime.now(timezone.utc); assert store.claim(job_id,"worker",10,now)
    barrier=threading.Barrier(2); outcomes=[]; lock=threading.Lock()
    def hb():
        barrier.wait()
        try: store.heartbeat(job_id,"worker",10,now+timedelta(seconds=1)); out="heartbeat"
        except JobLeaseError: out="rejected"
        with lock: outcomes.append(out)
    def bad():
        barrier.wait()
        try: store.fail(job_id,"worker","boom",now+timedelta(seconds=1)); out="failure"
        except JobLeaseError: out="rejected"
        with lock: outcomes.append(out)
    ts=[threading.Thread(target=hb),threading.Thread(target=bad)]
    [t.start() for t in ts]; [t.join() for t in ts]
    assert "failure" in outcomes
    assert store.get(job_id).status == JobStatus.FAILED
