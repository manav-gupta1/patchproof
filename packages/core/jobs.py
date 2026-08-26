from uuid import UUID

from packages.database.models import JobStatus


class JobService:
    """Domain-level job state transitions. Persistence is intentionally injected later."""

    @staticmethod
    def validate_transition(current: JobStatus, target: JobStatus) -> None:
        allowed = {
            JobStatus.QUEUED: {JobStatus.RUNNING, JobStatus.FAILED},
            JobStatus.RUNNING: {JobStatus.SUCCEEDED, JobStatus.FAILED},
            JobStatus.SUCCEEDED: set(),
            JobStatus.FAILED: set(),
        }
        if target not in allowed[current]:
            raise ValueError(f"Invalid job transition: {current} -> {target}")
