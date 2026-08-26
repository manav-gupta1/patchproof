from datetime import datetime, timedelta, timezone

from packages.jobs.crash_recovery import CrashRecovery


class Store:
    def __init__(self):
        self.state = {
            "job": {
                "status": "running",
                "worker_id": "worker-old",
                "lease_until": datetime.now(timezone.utc) + timedelta(seconds=1),
            }
        }

    def reconcile(self, now):
        job=self.state["job"]
        if job["status"]=="running" and job["lease_until"] <= now:
            job["status"]="queued"
            job["worker_id"]=None
            return {"recovered":["job"], "completed":[]}
        return {"recovered":[], "completed":[]}


class Reconciler:
    def __init__(self, store):
        self.store=store

    def reconcile(self, now=None):
        return self.store.reconcile(now)


def test_terminated_worker_is_recovered_after_restart():
    store=Store()
    recovery=CrashRecovery(Reconciler(store))
    now=datetime.now(timezone.utc)+timedelta(seconds=2)

    report=recovery.recover(now=now)

    assert report["recovered"]==["job"]
    assert store.state["job"]["status"]=="queued"
    assert store.state["job"]["worker_id"] is None


def test_restart_recovery_is_idempotent():
    store=Store()
    recovery=CrashRecovery(Reconciler(store))
    now=datetime.now(timezone.utc)+timedelta(seconds=2)

    first=recovery.recover(now=now)
    second=recovery.recover(now=now)

    assert first["recovered"]==["job"]
    assert second["recovered"]==[]
    assert store.state["job"]["status"]=="queued"


def test_live_worker_is_not_recovered():
    store=Store()
    recovery=CrashRecovery(Reconciler(store))
    now=datetime.now(timezone.utc)

    report=recovery.recover(now=now)

    assert report["recovered"]==[]
    assert store.state["job"]["status"]=="running"
