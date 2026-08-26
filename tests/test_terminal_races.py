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

def test_success_and_failure_race_has_exactly_one_terminal_winner():
    store=make(); job_id=store.create("terminal-race")
    now=datetime.now(timezone.utc); assert store.claim(job_id,"worker",10,now)
    barrier=threading.Barrier(2); outcomes=[]; lock=threading.Lock()
    def ok():
        barrier.wait()
        try: store.succeed(job_id,"worker",now+timedelta(seconds=1)); out="succeeded"
        except JobLeaseError: out="rejected"
        with lock: outcomes.append(out)
    def bad():
        barrier.wait()
        try: store.fail(job_id,"worker","boom",now+timedelta(seconds=1)); out="failed"
        except JobLeaseError: out="rejected"
        with lock: outcomes.append(out)
    ts=[threading.Thread(target=ok),threading.Thread(target=bad)]
    [t.start() for t in ts]; [t.join() for t in ts]
    assert sum(x in {"succeeded","failed"} for x in outcomes)==1
    assert outcomes.count("rejected")==1

def test_terminal_transition_loses_to_expired_lease():
    store=make(); job_id=store.create("expiry-race")
    now=datetime.now(timezone.utc); assert store.claim(job_id,"worker",1,now)
    expired=now+timedelta(seconds=2)
    with pytest.raises(JobLeaseError): store.succeed(job_id,"worker",expired)
    with pytest.raises(JobLeaseError): store.fail(job_id,"worker","late",expired)
    assert store.get(job_id).status == JobStatus.RUNNING

def test_terminal_state_cannot_be_overwritten():
    store=make(); job_id=store.create("terminal-lock")
    now=datetime.now(timezone.utc); assert store.claim(job_id,"worker",10,now)
    store.succeed(job_id,"worker",now+timedelta(seconds=1))
    with pytest.raises(JobLeaseError):
        store.fail(job_id,"worker","overwrite",now+timedelta(seconds=1))
    assert store.get(job_id).status == JobStatus.SUCCEEDED
