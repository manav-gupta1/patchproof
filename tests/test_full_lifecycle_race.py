from datetime import datetime, timedelta, timezone
import threading
from sqlalchemy import create_engine
from pathlib import Path
import tempfile

from packages.jobs.sql_store import SQLJobStore
from packages.jobs.worker import JobStatus


def make():
    path = Path(tempfile.mkstemp(suffix=".sqlite")[1])
    engine=create_engine(f"sqlite:///{path}")
    store=SQLJobStore(engine)
    store.create_schema()
    return store


def test_claim_heartbeat_terminal_lifecycle_under_contention():
    store=make()
    ids=[f"job-{i}" for i in range(12)]
    for job_id in ids:
        store.create(job_id)

    start=datetime.now(timezone.utc)
    outcomes=[]
    lock=threading.Lock()

    def worker(worker_id):
        for job_id in ids:
            if not store.claim(job_id, worker_id, lease_seconds=3, now=start):
                continue
            try:
                store.heartbeat(
                    job_id, worker_id, lease_seconds=3,
                    now=start + timedelta(seconds=1)
                )
                if int(job_id.rsplit("-", 1)[1]) % 2 == 0:
                    store.succeed(
                        job_id, worker_id,
                        now=start + timedelta(seconds=2)
                    )
                    outcome="succeeded"
                else:
                    store.fail(
                        job_id, worker_id, "boom",
                        now=start + timedelta(seconds=2)
                    )
                    outcome="failed"
            except Exception:
                outcome="rejected"
            with lock:
                outcomes.append((job_id, outcome))

    threads=[
        threading.Thread(target=worker, args=(f"worker-{i}",))
        for i in range(6)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert all(
        store.get(job_id).status in {JobStatus.SUCCEEDED, JobStatus.FAILED}
        for job_id in ids
    )
    terminal=[x for x in outcomes if x[1] in {"succeeded","failed"}]
    assert len(terminal) == 12


def test_expired_claim_recovered_then_new_owner_completes():
    store=make()
    job_id="recovery-race"
    store.create(job_id)
    start=datetime.now(timezone.utc)

    assert store.claim(job_id, "old", lease_seconds=1, now=start)
    expired=start + timedelta(seconds=2)

    with store.engine.begin() as conn:
        conn.execute(
            store.jobs.update()
            .where(store.jobs.c.job_id == job_id)
            .values(
                status=JobStatus.QUEUED.value,
                lease_owner=None,
                lease_until=None,
            )
        )

    assert store.claim(job_id, "new", lease_seconds=10, now=expired)
    store.succeed(job_id, "new", now=expired + timedelta(seconds=1))
    assert store.get(job_id).status == JobStatus.SUCCEEDED
