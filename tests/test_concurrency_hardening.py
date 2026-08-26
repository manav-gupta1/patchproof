import threading
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine

from packages.jobs.sql_store import SQLJobStore
from packages.jobs.retry_store import SQLRetryStore
from packages.jobs.retry_handoff import RetryHandoff
from packages.jobs.recovery_reconciler import RecoveryReconciler


def make():
    engine=create_engine("sqlite://", connect_args={"check_same_thread": False})
    jobs=SQLJobStore(engine); jobs.create_schema()
    retries=SQLRetryStore(engine); retries.create_schema()
    return engine,jobs,retries,RetryHandoff(engine,retries.jobs,jobs.jobs)


def test_only_one_worker_can_claim_same_retry():
    engine,jobs,retries,h=make()
    jobs.create("race")
    retries.record_retry("race",1,0,"x")
    barrier=threading.Barrier(2)
    results=[]

    def claim(worker):
        barrier.wait()
        results.append(h.claim("race",worker))

    a=threading.Thread(target=claim,args=("a",))
    b=threading.Thread(target=claim,args=("b",))
    a.start(); b.start(); a.join(); b.join()

    assert sum(x is not None for x in results)==1
    assert retries.get("race")["state"]=="dispatched"


def test_stale_worker_cannot_complete_after_recovery_requeue():
    engine,jobs,retries,h=make()
    jobs.create("stale")
    retries.record_retry("stale",1,0,"x")
    h.claim("stale","old",lease_seconds=1)

    now=datetime.now(timezone.utc)+timedelta(seconds=2)
    RecoveryReconciler(engine,retries.jobs,jobs.jobs).reconcile(now)

    assert retries.get("stale")["state"]=="queued"
    assert h.complete("stale","old") is False


def test_second_claim_wins_only_after_expiry_and_recovery():
    engine,jobs,retries,h=make()
    jobs.create("handoff")
    retries.record_retry("handoff",1,0,"x")
    h.claim("handoff","old",lease_seconds=1)

    # Still owned: another worker cannot claim.
    assert h.claim("handoff","new") is None

    now=datetime.now(timezone.utc)+timedelta(seconds=2)
    RecoveryReconciler(engine,retries.jobs,jobs.jobs).reconcile(now)

    assert h.claim("handoff","new",lease_seconds=60,now=now) is not None
    assert retries.get("handoff")["dispatch_owner"]=="new"
