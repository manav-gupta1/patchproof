from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from sqlalchemy import create_engine
from packages.jobs.sql_store import SQLJobStore
from packages.jobs.retry_store import SQLRetryStore
from packages.jobs.retry_handoff import RetryHandoff
from packages.jobs.retry_dispatcher import RetryDispatcher

def make():
    e=create_engine("sqlite://")
    j=SQLJobStore(e); j.create_schema()
    r=SQLRetryStore(e); r.create_schema()
    return j,r,RetryHandoff(e,r.jobs,j.jobs)

def test_crash_after_handoff_is_recoverable():
    jobs,retries,h=make()
    jobs.create("j"); retries.record_retry("j",2,0,"timeout")
    assert h.claim("j","a",lease_seconds=1)
    assert retries.get("j")["state"]=="dispatched"
    later=datetime.now(timezone.utc)+timedelta(seconds=2)
    assert h.recover_expired(later)==1
    assert retries.get("j")["state"]=="queued"

def test_token_deleted_only_after_completion():
    jobs,retries,h=make()
    jobs.create("j"); retries.record_retry("j",2,0,"x")
    h.claim("j","a")
    assert retries.get("j")["state"]=="dispatched"
    assert h.complete("j","a")
    assert retries.get("j") is None

def test_wrong_worker_cannot_complete():
    jobs,retries,h=make()
    jobs.create("j"); retries.record_retry("j",2,0,"x")
    h.claim("j","a")
    assert not h.complete("j","b")
    assert retries.get("j")["state"]=="dispatched"

def test_dispatch_runs_worker_then_completes():
    jobs,retries,h=make()
    jobs.create("j"); retries.record_retry("j",3,0,"x")
    calls=[]
    class W:
        def run(self,*,job,worker_id,**kwargs):
            calls.append((job.job_id,worker_id)); return True
    d=RetryDispatcher(h,W(),lambda jid:(SimpleNamespace(job_id=jid),{"patch_diff":"d","title":"t","body":"b","head":"h","base":"main"}))
    out=d.dispatch_due(worker_id="a")
    assert out[0]["status"]=="succeeded"
    assert calls==[("j","a")]
    assert retries.get("j") is None
