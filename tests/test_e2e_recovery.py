from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from sqlalchemy import create_engine

from packages.jobs.sql_store import SQLJobStore
from packages.jobs.retry_store import SQLRetryStore
from packages.jobs.retry_handoff import RetryHandoff
from packages.jobs.retry_dispatcher import RetryDispatcher
from packages.jobs.recovery_reconciler import RecoveryReconciler
from packages.jobs.recovery_metrics import RecoveryMetrics, RecoveryRunObserver


class PipelineWorker:
    def __init__(self):
        self.calls = []
        self.fail_once = True

    def run(self, *, job, worker_id, **kwargs):
        self.calls.append((job.job_id, worker_id))
        if self.fail_once:
            self.fail_once = False
            raise RuntimeError("verification backend temporarily unavailable")
        return True


def make_system():
    engine = create_engine("sqlite://")
    jobs = SQLJobStore(engine)
    jobs.create_schema()
    retries = SQLRetryStore(engine)
    retries.create_schema()
    handoff = RetryHandoff(engine, retries.jobs, jobs.jobs)
    return engine, jobs, retries, handoff


def test_crash_recovery_retry_pipeline_end_to_end():
    engine, jobs, retries, handoff = make_system()
    jobs.create("job-e2e")
    retries.record_retry("job-e2e", 1, 0, "initial transient failure")

    # Dispatcher claims the retry but crashes before the worker starts.
    claimed = handoff.claim("job-e2e", "worker-a", lease_seconds=1)
    assert claimed is not None
    assert retries.get("job-e2e")["state"] == "dispatched"

    # Lease expires; reconciler restores the durable retry.
    expired = datetime.now(timezone.utc) + timedelta(seconds=2)
    recovery = RecoveryReconciler(engine, retries.jobs, jobs.jobs)
    assert recovery.reconcile(expired)["recovered"] == ["job-e2e"]
    assert retries.get("job-e2e")["state"] == "queued"

    # A second worker can now execute the recovered retry.
    worker = PipelineWorker()
    dispatcher = RetryDispatcher(
        handoff,
        worker,
        lambda jid: (
            SimpleNamespace(job_id=jid),
            {
                "patch_diff": "diff",
                "title": "verification",
                "body": "body",
                "head": "head",
                "base": "main",
            },
        ),
    )

    # First real execution fails transiently; the handoff remains durable.
    first = dispatcher.dispatch_due(worker_id="worker-b")
    assert first[0]["status"] == "failed"
    assert retries.get("job-e2e")["state"] == "dispatched"

    # Simulate the retry policy persisting a new attempt after the transient
    # worker failure has been observed.
    retries.record_retry("job-e2e", 2, 0, "verification backend unavailable")
    assert retries.get("job-e2e")["state"] == "queued"

    second = dispatcher.dispatch_due(worker_id="worker-c")
    assert second[0]["status"] == "succeeded"
    assert len(worker.calls) == 2
    assert retries.get("job-e2e") is None


def test_observability_wraps_recovery_in_same_e2e_path():
    engine, jobs, retries, handoff = make_system()
    jobs.create("job-metrics")
    retries.record_retry("job-metrics", 1, 0, "x")
    handoff.claim("job-metrics", "worker-a", lease_seconds=1)

    now = datetime.now(timezone.utc) + timedelta(seconds=2)
    metrics = RecoveryMetrics()
    observer = RecoveryRunObserver(RecoveryReconciler(engine, retries.jobs, jobs.jobs), metrics)

    result = observer.run_once(now=now)
    snapshot = metrics.snapshot()

    assert result["recovered"] == ["job-metrics"]
    assert snapshot["runs"] == 1
    assert snapshot["recovered"] == 1
    assert snapshot["failures"] == 0
