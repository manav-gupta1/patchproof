from types import SimpleNamespace
from sqlalchemy import create_engine

from packages.jobs.sql_store import SQLJobStore
from packages.jobs.retry_store import SQLRetryStore
from packages.jobs.retry_handoff import RetryHandoff
from packages.jobs.retry_dispatcher import RetryDispatcher


def make():
    engine = create_engine("sqlite://")
    jobs = SQLJobStore(engine)
    jobs.create_schema()
    retries = SQLRetryStore(engine)
    retries.create_schema()
    handoff = RetryHandoff(engine, retries.jobs, jobs.jobs)
    return engine, jobs, retries, handoff


def test_lease_and_retry_consumption_commit_together():
    _, jobs, retries, handoff = make()
    jobs.create("job-1")
    retries.record_retry("job-1", 4, 0, "timeout")

    result = handoff.claim("job-1", "worker-a")
    assert result["attempt"] == 4
    assert retries.get("job-1")["state"] == "dispatched"
    assert jobs.get("job-1").lease_owner == "worker-a"


def test_claim_is_atomic_against_second_worker():
    _, jobs, retries, handoff = make()
    jobs.create("job-2")
    retries.record_retry("job-2", 2, 0, "timeout")

    assert handoff.claim("job-2", "worker-a") is not None
    assert handoff.claim("job-2", "worker-b") is None
    assert retries.get("job-2")["state"] == "dispatched"


def test_future_retry_is_not_consumed():
    _, jobs, retries, handoff = make()
    jobs.create("job-3")
    retries.record_retry("job-3", 2, 3600, "timeout")

    assert handoff.claim("job-3", "worker-a") is None
    assert retries.get("job-3") is not None
    assert jobs.get("job-3").lease_owner is None


def test_dispatch_executes_after_atomic_handoff():
    _, jobs, retries, handoff = make()
    jobs.create("job-4")
    retries.record_retry("job-4", 3, 0, "timeout")
    calls = []

    class Worker:
        def run(self, *, job, worker_id, **kwargs):
            calls.append((job.job_id, worker_id))
            return True

    dispatcher = RetryDispatcher(
        handoff, Worker(),
        lambda jid: (
            SimpleNamespace(job_id=jid),
            {"patch_diff": "d", "title": "t", "body": "b",
             "head": "h", "base": "main"},
        ),
    )

    result = dispatcher.dispatch_due(worker_id="worker-a")
    assert result[0]["status"] == "succeeded"
    assert calls == [("job-4", "worker-a")]
    assert retries.get("job-4") is None
