from packages.jobs.recovery_scheduler import RecoveryScheduler

class Reconciler:
    def __init__(self):
        self.calls=0
    def reconcile(self, now=None):
        self.calls += 1
        return {"recovered": [], "completed": []}

def test_run_once_delegates_to_reconciler():
    r=Reconciler()
    s=RecoveryScheduler(r, interval_seconds=1)
    assert s.run_once()["recovered"] == []
    assert r.calls == 1

def test_scheduler_can_start_and_stop():
    r=Reconciler()
    s=RecoveryScheduler(r, interval_seconds=1)
    s.start()
    s.stop()
    assert r.calls >= 1

def test_invalid_interval_rejected():
    r=Reconciler()
    try:
        RecoveryScheduler(r, interval_seconds=0)
        assert False
    except ValueError:
        assert True
