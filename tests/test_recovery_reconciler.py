from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from packages.jobs.sql_store import SQLJobStore
from packages.jobs.retry_store import SQLRetryStore
from packages.jobs.retry_handoff import RetryHandoff
from packages.jobs.recovery_reconciler import RecoveryReconciler

def make():
    e=create_engine("sqlite://")
    j=SQLJobStore(e); j.create_schema()
    r=SQLRetryStore(e); r.create_schema()
    return e,j,r,RetryHandoff(e,r.jobs,j.jobs)

def test_expired_dispatch_is_requeued():
    e,j,r,h=make()
    j.create("j"); r.record_retry("j",2,0,"x")
    h.claim("j","worker-a",lease_seconds=1)
    now=datetime.now(timezone.utc)+timedelta(seconds=2)
    out=RecoveryReconciler(e,r.jobs,j.jobs).reconcile(now)
    assert out["recovered"]==["j"]
    assert r.get("j")["state"]=="queued"

def test_expired_dispatch_for_successful_job_is_finalized():
    e,j,r,h=make()
    j.create("j"); r.record_retry("j",2,0,"x")
    h.claim("j","worker-a",lease_seconds=1)
    j.succeed("j","worker-a")
    now=datetime.now(timezone.utc)+timedelta(seconds=2)
    out=RecoveryReconciler(e,r.jobs,j.jobs).reconcile(now)
    assert out["completed"]==["j"]
    assert r.get("j") is None

def test_missing_job_is_not_deleted():
    e,j,r,h=make()
    r.record_retry("missing",2,0,"x")
    # No dispatched row: reconciliation must not touch unrelated queued work.
    out=RecoveryReconciler(e,r.jobs,j.jobs).reconcile()
    assert out=={"recovered":[],"completed":[]}
    assert r.get("missing") is not None
