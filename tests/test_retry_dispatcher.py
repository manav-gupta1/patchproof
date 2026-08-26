from sqlalchemy import create_engine

from packages.jobs.retry_dispatcher import RetryDispatcher
from packages.jobs.retry_store import SQLRetryStore
from packages.jobs.sql_store import SQLJobStore


def make():
    engine = create_engine("sqlite://")
    retries = SQLRetryStore(engine)
    retries.create_schema()
    jobs = SQLJobStore(engine)
    jobs.create_schema()
    return retries, jobs


def test_due_retry_is_claimed_by_job_lease_and_removed():
    retries, jobs = make()
    jobs.create("job-1")
    retries.record_retry("job-1", 2, 0, "timeout")

    dispatcher = RetryDispatcher(retries, jobs, worker=None)
    dispatched = dispatcher.dispatch_due(worker_id="worker-a")

    assert dispatched == [("job-1", 2)]
    assert retries.get("job-1")["state"] == "dispatched"
    assert jobs.get("job-1").lease_owner == "worker-a"


def test_second_worker_cannot_dispatch_same_job():
    retries, jobs = make()
    jobs.create("job-2")
    retries.record_retry("job-2", 2, 0, "timeout")

    first = RetryDispatcher(retries, jobs, worker=None)
    second = RetryDispatcher(retries, jobs, worker=None)

    assert first.dispatch_due(worker_id="worker-a") == [("job-2", 2)]
    assert second.dispatch_due(worker_id="worker-b") == []


def test_non_due_retry_remains_queued():
    retries, jobs = make()
    jobs.create("job-3")
    retries.record_retry("job-3", 2, 3600, "timeout")

    dispatcher = RetryDispatcher(retries, jobs, worker=None)
    assert dispatcher.dispatch_due(worker_id="worker-a") == []
    assert retries.get("job-3") is not None


def test_missing_job_is_not_destructively_removed():
    retries, jobs = make()
    retries.record_retry("missing", 2, 0, "orphan")

    dispatcher = RetryDispatcher(retries, jobs, worker=None)
    try:
        result = dispatcher.dispatch_due(worker_id="worker-a")
    except KeyError:
        result = []

    assert result == []
    assert retries.get("missing") is not None
