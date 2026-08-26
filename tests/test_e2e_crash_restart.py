from datetime import datetime, timedelta, timezone

from packages.jobs.production_runtime import ProductionRuntime
from packages.jobs.crash_recovery import CrashRecovery


class Store:
    def __init__(self):
        self.job = {
            "status": "queued",
            "worker_id": None,
            "lease_until": None,
            "result": None,
        }

    def claim(self, worker, now):
        if self.job["status"] != "queued":
            return False
        self.job.update(
            status="running",
            worker_id=worker,
            lease_until=now + timedelta(seconds=1),
        )
        return True

    def recover(self, now):
        if (
            self.job["status"] == "running"
            and self.job["lease_until"] <= now
        ):
            self.job.update(status="queued", worker_id=None, lease_until=None)
            return {"recovered": ["job"], "completed": []}
        return {"recovered": [], "completed": []}

    def complete(self, worker, now, result):
        if (
            self.job["status"] != "running"
            or self.job["worker_id"] != worker
            or self.job["lease_until"] <= now
        ):
            return False
        self.job.update(
            status="succeeded",
            worker_id=None,
            lease_until=None,
            result=result,
        )
        return True


class Reconciler:
    def __init__(self, store):
        self.store=store

    def reconcile(self, now=None):
        return self.store.recover(now)


class Lifecycle:
    def __init__(self):
        self.running=False
        self.draining=False

    def start(self):
        self.running=True

    def stop(self, timeout=30):
        self.draining=True
        self.running=False

    def is_running(self):
        return self.running


def test_full_crash_restart_recovery_reclaim_and_completion():
    store=Store()
    life=Lifecycle()

    first=ProductionRuntime(Reconciler(store), life)
    t0=datetime.now(timezone.utc)
    first.start(now=t0)

    assert store.claim("worker-a", t0)
    assert store.job["status"]=="running"

    # Simulate a hard process crash: no graceful stop and no completion.
    life.running=False

    restart=ProductionRuntime(Reconciler(store), Lifecycle())
    restart.start(now=t0+timedelta(seconds=2))

    assert store.job["status"]=="queued"
    assert store.job["worker_id"] is None

    t1=t0+timedelta(seconds=2)
    assert store.claim("worker-b", t1)
    assert store.complete("worker-b", t1, {"ok": True})

    assert store.job["status"]=="succeeded"
    assert store.job["result"]=={"ok": True}


def test_stale_first_worker_cannot_complete_after_restart():
    store=Store()
    t0=datetime.now(timezone.utc)
    assert store.claim("worker-a", t0)

    restart=CrashRecovery(Reconciler(store))
    t1=t0+timedelta(seconds=2)
    restart.recover(now=t1)

    assert store.claim("worker-b", t1)
    assert store.complete("worker-a", t1, {"stale": True}) is False
    assert store.complete("worker-b", t1, {"authoritative": True}) is True
    assert store.job["result"]=={"authoritative": True}
