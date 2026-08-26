from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from packages.orchestration.models import FailureCode, JobState, RemediationJob


ALLOWED: dict[JobState, set[JobState]] = {
    JobState.RECEIVED: {JobState.ANALYZING, JobState.FAILED},
    JobState.ANALYZING: {JobState.EXPLOITING, JobState.FAILED},
    JobState.EXPLOITING: {JobState.PATCHING, JobState.FAILED},
    JobState.PATCHING: {JobState.VERIFYING, JobState.FAILED},
    JobState.VERIFYING: {JobState.VERIFIED, JobState.FAILED},
    JobState.VERIFIED: {JobState.PR_CREATED},
    JobState.PR_CREATED: set(),
    JobState.FAILED: set(),
}


class InvalidTransition(ValueError):
    pass


class JobStateMachine:
    def transition(self, job: RemediationJob, target: JobState) -> RemediationJob:
        if target not in ALLOWED[job.state]:
            raise InvalidTransition(f"{job.state.value} -> {target.value} is not allowed")
        job.state = target
        job.updated_at = datetime.now(timezone.utc)
        return job

    def fail(
        self,
        job: RemediationJob,
        code: FailureCode,
        message: str,
    ) -> RemediationJob:
        if job.state is not JobState.FAILED:
            if JobState.FAILED not in ALLOWED[job.state]:
                raise InvalidTransition(f"{job.state.value} -> failed is not allowed")
            job.state = JobState.FAILED
        job.failure_code = code
        job.failure_message = message
        job.updated_at = datetime.now(timezone.utc)
        return job
