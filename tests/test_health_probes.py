from packages.jobs.health import HealthProbe
from packages.jobs.probe_service import ProbeService
from packages.jobs.readiness import ReadinessProbe

class Lifecycle:
    def __init__(self, running=True, draining=False):
        self.running=running
        self.draining=draining
    def is_running(self):
        return self.running

class Recovery:
    def __init__(self, ready=True):
        self.ready=ready

def test_liveness_is_healthy_while_process_is_running():
    assert HealthProbe(Lifecycle(True)).check().healthy is True

def test_liveness_is_unhealthy_when_process_is_stopped():
    assert HealthProbe(Lifecycle(False)).check().healthy is False

def test_liveness_does_not_fail_just_because_worker_is_draining():
    assert HealthProbe(Lifecycle(True, True)).check().healthy is True

def test_combined_status_keeps_health_and_readiness_separate():
    p=ProbeService(
        HealthProbe(Lifecycle(True, True)),
        ReadinessProbe(Recovery(True), Lifecycle(True, True)),
    )
    s=p.status()
    assert s["healthy"] is True
    assert s["ready"] is False
    assert s["readiness_reason"]=="worker_draining"
