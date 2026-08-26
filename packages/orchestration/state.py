from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class JobState(str, Enum):
    RECEIVED = "RECEIVED"
    CONTEXT_READY = "CONTEXT_READY"
    PATCH_PROPOSED = "PATCH_PROPOSED"
    PATCH_VALIDATED = "PATCH_VALIDATED"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"
    PROMOTING = "PROMOTING"
    PR_CREATED = "PR_CREATED"
    REJECTED = "REJECTED"


_ALLOWED = {
    JobState.RECEIVED: {JobState.CONTEXT_READY, JobState.REJECTED},
    JobState.CONTEXT_READY: {JobState.PATCH_PROPOSED, JobState.REJECTED},
    JobState.PATCH_PROPOSED: {JobState.PATCH_VALIDATED, JobState.REJECTED},
    JobState.PATCH_VALIDATED: {JobState.VERIFYING, JobState.REJECTED},
    JobState.VERIFYING: {JobState.VERIFIED, JobState.REJECTED},
    JobState.VERIFIED: {JobState.PROMOTING, JobState.REJECTED},
    JobState.PROMOTING: {JobState.PR_CREATED, JobState.REJECTED},
    JobState.PR_CREATED: set(),
    JobState.REJECTED: set(),
}


@dataclass
class JobRecord:
    job_id: str
    state: JobState = JobState.RECEIVED
    history: list[JobState] = field(default_factory=lambda: [JobState.RECEIVED])
    error: str | None = None
    evidence: dict = field(default_factory=dict)


class JobStore:
    """In-memory state store for the orchestration contract; PostgreSQL is the production adapter."""
    def __init__(self):
        self.jobs: dict[str, JobRecord] = {}

    def create(self, job_id: str) -> JobRecord:
        if job_id in self.jobs:
            return self.jobs[job_id]
        self.jobs[job_id] = JobRecord(job_id)
        return self.jobs[job_id]

    def transition(self, job_id: str, state: JobState, *, error: str | None = None):
        job = self.jobs[job_id]
        if state not in _ALLOWED[job.state]:
            raise ValueError(f"invalid transition {job.state} -> {state}")
        job.state = state
        job.history.append(state)
        if error:
            job.error = error
        return job

    def reject(self, job_id: str, error: str):
        job = self.jobs[job_id]
        if job.state != JobState.REJECTED:
            if JobState.REJECTED not in _ALLOWED[job.state]:
                raise ValueError(f"cannot reject from {job.state}")
            job.state = JobState.REJECTED
            job.history.append(JobState.REJECTED)
        job.error = error
        return job
