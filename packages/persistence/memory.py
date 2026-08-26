from __future__ import annotations

from datetime import datetime, timezone

from packages.persistence.models import JobState, RemediationJob


class MemoryJobRepository:
    def __init__(self) -> None:
        self.jobs: dict[str, RemediationJob] = {}

    def create(self, job: RemediationJob) -> RemediationJob:
        if job.id in self.jobs:
            raise ValueError("job already exists")
        self.jobs[job.id] = job
        return job

    def get(self, job_id: str) -> RemediationJob | None:
        return self.jobs.get(job_id)

    def transition(self, job_id: str, state: JobState) -> RemediationJob:
        job = self.jobs[job_id]
        job.state = state
        job.updated_at = datetime.now(timezone.utc)
        self.jobs[job_id] = job
        return job
