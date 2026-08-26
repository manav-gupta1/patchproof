from packages.jobs.readiness import ReadinessProbe

class Recovery:
    def __init__(self, ready=False):
        self.ready=ready

class Lifecycle:
    def __init__(self, running=True, draining=False):
        self.running=running
        self.draining=draining
    def is_running(self):
        return self.running

def test_not_ready_until_startup_recovery_finishes():
    p=ReadinessProbe(Recovery(False), Lifecycle())
    s=p.check()
    assert s.ready is False
    assert s.reason=="startup_recovery_incomplete"

def test_not_ready_when_worker_is_stopped():
    p=ReadinessProbe(Recovery(True), Lifecycle(False))
    s=p.check()
    assert s.ready is False
    assert s.reason=="worker_not_running"

def test_draining_worker_is_not_ready():
    p=ReadinessProbe(Recovery(True), Lifecycle(True, True))
    s=p.check()
    assert s.ready is False
    assert s.reason=="worker_draining"

def test_ready_only_when_recovery_and_worker_are_healthy():
    p=ReadinessProbe(Recovery(True), Lifecycle(True, False))
    s=p.check()
    assert s.ready is True
    assert s.reason=="ready"
