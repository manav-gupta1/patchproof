import pytest
from packages.jobs.startup_recovery import StartupRecovery
from packages.jobs.worker_bootstrap import WorkerBootstrap


class Reconciler:
    def __init__(self):
        self.calls=0
    def reconcile(self, now=None):
        self.calls += 1
        return {"recovered":["a","b"], "completed":["c"]}


class Lifecycle:
    def __init__(self):
        self.calls=[]
    def start(self):
        self.calls.append("start")
    def stop(self, timeout=30):
        self.calls.append(("stop",timeout))


def test_startup_recovery_runs_before_worker_is_ready():
    r=Reconciler()
    s=StartupRecovery(r)
    report=s.initialize()
    assert report.recovered == 2
    assert report.completed == 1
    assert s.ready is True
    assert r.calls == 1


def test_worker_cannot_be_marked_ready_without_recovery():
    s=StartupRecovery(Reconciler())
    with pytest.raises(RuntimeError):
        s.require_ready()


def test_bootstrap_recovers_before_polling_starts():
    events=[]
    class R:
        def reconcile(self, now=None):
            events.append("recover")
            return {"recovered":[],"completed":[]}
    class L:
        def start(self):
            events.append("start")
        def stop(self, timeout=30):
            events.append("stop")

    b=WorkerBootstrap(StartupRecovery(R()), L())
    b.start()
    assert events == ["recover","start"]


def test_bootstrap_stop_delegates():
    l=Lifecycle()
    b=WorkerBootstrap(StartupRecovery(Reconciler()), l)
    b.stop(timeout=9)
    assert l.calls == [("stop",9)]
