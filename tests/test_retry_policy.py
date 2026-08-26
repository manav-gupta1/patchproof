from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine

from packages.jobs.retry_policy import (
    PermanentJobError, RetryPolicy, FailureClass
)
from packages.jobs.retry_store import SQLRetryStore


def test_retryable_failure_uses_exponential_backoff():
    p = RetryPolicy(max_attempts=5, base_delay=10, max_delay=100, jitter=0)
    d1 = p.decide(RuntimeError("network"), 1)
    d2 = p.decide(RuntimeError("network"), 2)
    d3 = p.decide(RuntimeError("network"), 3)

    assert d1.failure_class == FailureClass.RETRYABLE
    assert d1.retry and d1.delay_seconds == 10
    assert d2.delay_seconds == 20
    assert d3.delay_seconds == 40


def test_backoff_is_bounded_and_budget_is_finite():
    p = RetryPolicy(max_attempts=3, base_delay=10, max_delay=25, jitter=0)
    assert p.decide(RuntimeError("x"), 3).retry is False
    assert p.decide(RuntimeError("x"), 2).delay_seconds == 20
    assert p.decide(RuntimeError("x"), 4).retry is False


def test_permanent_failure_is_not_retried():
    p = RetryPolicy()
    decision = p.decide(PermanentJobError("bad patch"), 1)
    assert decision.failure_class == FailureClass.PERMANENT
    assert decision.retry is False


def test_retry_schedule_is_durable():
    engine = create_engine("sqlite://")
    store = SQLRetryStore(engine)
    store.create_schema()
    store.record_retry("job-1", 2, 0, "network")

    row = store.get("job-1")
    assert row["attempts"] == 2
    assert row["last_error"] == "network"
    assert row["next_run_at"] <= datetime.now(timezone.utc)


def test_due_retries_can_be_discovered():
    engine = create_engine("sqlite://")
    store = SQLRetryStore(engine)
    store.create_schema()
    store.record_retry("job-2", 2, 0, "timeout")
    assert [r["job_id"] for r in store.due()] == ["job-2"]
