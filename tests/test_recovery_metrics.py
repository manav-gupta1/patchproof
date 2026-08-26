import pytest
from packages.jobs.recovery_metrics import RecoveryMetrics, RecoveryRunObserver

class R:
    def __init__(self, fail=False):
        self.fail=fail
    def reconcile(self, now=None):
        if self.fail: raise RuntimeError("db down")
        return {"recovered":["a","b"], "completed":["c"]}

def test_metrics_capture_recovery_counts():
    m=RecoveryMetrics()
    out=RecoveryRunObserver(R(),m).run_once()
    assert out["recovered"] == ["a","b"]
    assert m.snapshot()["runs"] == 1
    assert m.snapshot()["recovered"] == 2
    assert m.snapshot()["completed"] == 1
    assert m.snapshot()["failures"] == 0

def test_metrics_capture_failures():
    m=RecoveryMetrics()
    with pytest.raises(RuntimeError):
        RecoveryRunObserver(R(True),m).run_once()
    s=m.snapshot()
    assert s["runs"] == 1
    assert s["failures"] == 1

def test_snapshot_is_stable_copy():
    m=RecoveryMetrics()
    s=m.snapshot()
    s["runs"]=99
    assert m.snapshot()["runs"] == 0
