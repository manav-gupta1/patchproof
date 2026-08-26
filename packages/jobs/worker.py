from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class JobLeaseError(RuntimeError):
    pass


@dataclass(frozen=True)
class JobRecord:
    job_id: str
    status: JobStatus
    attempts: int
    lease_owner: str | None
    lease_until: datetime | None
    last_error: str | None = None


class InMemoryJobStore:
    def __init__(self):
        self.jobs = {}

    def create(self, job_id):
        self.jobs[job_id] = JobRecord(
            job_id, JobStatus.QUEUED, 0, None, None
        )

    def get(self, job_id):
        return self.jobs[job_id]

    def claim(self, job_id, worker_id, lease_seconds=60, now=None):
        now = now or datetime.now(timezone.utc)
        job = self.get(job_id)

        if job.status == JobStatus.SUCCEEDED:
            return False
        if (
            job.lease_owner is not None
            and job.lease_until is not None
            and job.lease_until > now
            and job.lease_owner != worker_id
        ):
            return False

        self.jobs[job_id] = JobRecord(
            job_id=job_id,
            status=JobStatus.RUNNING,
            attempts=job.attempts + 1,
            lease_owner=worker_id,
            lease_until=now + timedelta(seconds=lease_seconds),
            last_error=None,
        )
        return True

    def heartbeat(self, job_id, worker_id, lease_seconds=60, now=None):
        now = now or datetime.now(timezone.utc)
        job = self.get(job_id)
        if job.lease_owner != worker_id or not job.lease_until or job.lease_until <= now:
            raise JobLeaseError("worker lease is not valid")
        self.jobs[job_id] = JobRecord(
            job.job_id, job.status, job.attempts, worker_id,
            now + timedelta(seconds=lease_seconds), job.last_error
        )

    def succeed(self, job_id, worker_id):
        job = self.get(job_id)
        if job.lease_owner != worker_id:
            raise JobLeaseError("worker does not own job")
        self.jobs[job_id] = JobRecord(
            job.job_id, JobStatus.SUCCEEDED, job.attempts,
            None, None, None
        )

    def fail(self, job_id, worker_id, error):
        job = self.get(job_id)
        if job.lease_owner != worker_id:
            raise JobLeaseError("worker does not own job")
        self.jobs[job_id] = JobRecord(
            job.job_id, JobStatus.FAILED, job.attempts,
            None, None, error[:2000]
        )


class JobWorker:
    def __init__(self, store, worker_id, lease_seconds=60):
        self.store = store
        self.worker_id = worker_id
        self.lease_seconds = lease_seconds

    def run_once(self, job_id, handler):
        if not self.store.claim(job_id, self.worker_id, self.lease_seconds):
            return False

        try:
            handler()
        except Exception as exc:
            self.store.fail(job_id, self.worker_id, str(exc))
            raise
        else:
            self.store.succeed(job_id, self.worker_id)
            return True
