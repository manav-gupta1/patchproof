from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from packages.jobs.sql_store import SQLJobStore
from packages.jobs.worker import JobStatus, JobLeaseError


def store():
    engine = create_engine("sqlite://")
    s = SQLJobStore(engine)
    s.create_schema()
    return s


def test_atomic_claim_allows_only_one_live_owner():
    s = store()
    s.create("job-sql")
    now = datetime.now(timezone.utc)

    assert s.claim("job-sql", "worker-a", now=now)
    assert not s.claim("job-sql", "worker-b", now=now)
    assert s.get("job-sql").lease_owner == "worker-a"


def test_expired_lease_can_be_reclaimed_atomically():
    s = store()
    s.create("job-expired")
    now = datetime.now(timezone.utc)

    assert s.claim("job-expired", "worker-a", lease_seconds=1, now=now)
    later = now + timedelta(seconds=2)
    assert s.claim("job-expired", "worker-b", now=later)
    record = s.get("job-expired")
    assert record.lease_owner == "worker-b"
    assert record.attempts == 2


def test_old_owner_cannot_complete_after_reclaim():
    s = store()
    s.create("job-fence")
    now = datetime.now(timezone.utc)

    s.claim("job-fence", "worker-a", lease_seconds=1, now=now)
    s.claim("job-fence", "worker-b", now=now + timedelta(seconds=2))

    try:
        s.succeed("job-fence", "worker-a")
        assert False
    except JobLeaseError:
        assert True

    s.succeed("job-fence", "worker-b")
    assert s.get("job-fence").status == JobStatus.SUCCEEDED


def test_heartbeat_requires_current_live_owner():
    s = store()
    s.create("job-heartbeat")
    now = datetime.now(timezone.utc)
    s.claim("job-heartbeat", "worker-a", now=now)

    s.heartbeat("job-heartbeat", "worker-a", now=now)
    try:
        s.heartbeat(
            "job-heartbeat", "worker-b",
            now=now + timedelta(seconds=1)
        )
        assert False
    except JobLeaseError:
        assert True
