from packages.jobs.production_runtime import ProductionRuntime


class Reconciler:
    def __init__(self, events):
        self.events=events
    def reconcile(self, now=None):
        self.events.append("recover")
        return {"recovered":["stale"], "completed":[]}


class Lifecycle:
    def __init__(self, events):
        self.events=events
        self.running=False
        self.draining=False
    def start(self):
        self.events.append("worker_start")
        self.running=True
        self.draining=False
    def stop(self, timeout=30):
        self.events.append(("worker_stop",timeout))
        self.draining=True
        self.running=False
    def is_running(self):
        return self.running


def test_runtime_composes_recovery_before_worker_start():
    events=[]
    rt=ProductionRuntime(Reconciler(events), Lifecycle(events))
    report=rt.start()
    assert report.recovered == 1
    assert events == ["recover","worker_start"]
    assert rt.state().started is True
    assert rt.state().ready is True


def test_runtime_reports_not_ready_after_stop():
    events=[]
    life=Lifecycle(events)
    rt=ProductionRuntime(Reconciler(events), life)
    rt.start()
    rt.stop(timeout=5)
    assert events[-1] == ("worker_stop",5)
    assert rt.state().started is False
    assert rt.probes.readiness().ready is False


def test_runtime_is_not_ready_before_start():
    events=[]
    life=Lifecycle(events)
    rt=ProductionRuntime(Reconciler(events), life)
    assert rt.state().ready is False
