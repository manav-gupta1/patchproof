from types import SimpleNamespace
from sqlalchemy import create_engine

from packages.jobs.retry_dispatcher import RetryDispatcher
from packages.jobs.retry_store import SQLRetryStore
from packages.jobs.sql_store import SQLJobStore


class Worker:
    def __init__(self):
        self.calls = []

    def run(self, *, job, worker_id, **kwargs):
        self.calls.append((job.job_id, worker_id, kwargs))
        return True


def make():
    engine = create_engine("sqlite://")
    retries = SQLRetryStore(engine)
    retries.create_schema()
    jobs = SQLJobStore(engine)
    jobs.create_schema()
    return retries, jobs


def test_due_retry_executes_real_worker_pipeline():
    retries, jobs = make()
    jobs.create("job-run")
    retries.record_retry("job-run", 3, 0, "timeout")

    worker = Worker()

    def load(job_id):
        return (
            SimpleNamespace(job_id=job_id),
            {"patch_diff": "diff", "title": "t", "body": "b",
             "head": "h", "base": "main"},
        )

    dispatcher = RetryDispatcher(retries, jobs, worker, load)
    results = dispatcher.dispatch_due(worker_id="worker-a")

    assert results[0]["status"] == "succeeded"
    assert worker.calls[0][0] .__str__() == "job-run"
    assert retries.get("job-run") is None


def test_second_worker_cannot_execute_same_retry():
    retries, jobs = make()
    jobs.create("job-race")
    retries.record_retry("job-race", 2, 0, "timeout")

    worker_a = Worker()
    worker_b = Worker()

    load = lambda jid: (
        SimpleNamespace(job_id=jid),
        {"patch_diff": "d", "title": "t", "body": "b",
         "head": "h", "base": "main"},
    )

    a = RetryDispatcher(retries, jobs, worker_a, load)
    b = RetryDispatcher(retries, jobs, worker_b, load)

    assert len(a.dispatch_due(worker_id="a")) == 1
    assert len(b.dispatch_due(worker_id="b")) == 0
    assert len(worker_a.calls) == 1
    assert len(worker_b.calls) == 0


def test_job_loader_failure_does_not_create_a_second_execution():
    retries, jobs = make()
    jobs.create("job-load")
    retries.record_retry("job-load", 2, 0, "timeout")

    worker = Worker()

    def broken_loader(_):
        raise RuntimeError("job payload unavailable")

    dispatcher = RetryDispatcher(
        retries, jobs, worker, broken_loader
    )
    result = dispatcher.dispatch_due(worker_id="worker-a")

    assert result[0]["status"] == "failed"
    assert "payload unavailable" in result[0]["error"]
    assert worker.calls == []
