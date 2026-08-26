import json
from packages.jobs.health import HealthProbe
from packages.jobs.readiness import ReadinessProbe
from packages.jobs.probe_service import ProbeService
from packages.jobs.probe_http import ProbeHTTP

class Lifecycle:
    def __init__(self, running=True, draining=False):
        self.running=running
        self.draining=draining
    def is_running(self):
        return self.running

class Recovery:
    def __init__(self, ready=True):
        self.ready=ready

def service(running=True, recovery=True, draining=False):
    life=Lifecycle(running, draining)
    return ProbeService(HealthProbe(life), ReadinessProbe(Recovery(recovery), life))

def test_health_returns_200_when_process_is_alive():
    response=ProbeHTTP(service()).health()
    assert response["status"] == 200
    assert json.loads(response["body"])["checks"]["process_running"] is True

def test_health_returns_503_when_process_is_stopped():
    response=ProbeHTTP(service(running=False)).health()
    assert response["status"] == 503

def test_readiness_returns_200_when_ready():
    response=ProbeHTTP(service()).readiness()
    assert response["status"] == 200
    assert json.loads(response["body"])["reason"] == "ready"

def test_readiness_returns_503_during_startup():
    response=ProbeHTTP(service(recovery=False)).readiness()
    assert response["status"] == 503
    assert json.loads(response["body"])["reason"] == "startup_recovery_incomplete"

def test_readiness_returns_503_during_drain():
    response=ProbeHTTP(service(draining=True)).readiness()
    assert response["status"] == 503
    assert json.loads(response["body"])["reason"] == "worker_draining"
