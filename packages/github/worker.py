from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class RemediationJob:
    repository: str
    installation_id: int | None
    delivery_id: str
    finding: dict


class GitHubRemediationWorker:
    """
    Application boundary between webhook ingestion and remediation.
    Queue implementation is injected; this keeps GitHub concerns out of
    the remediation engine.
    """

    def __init__(self, queue):
        self.queue = queue

    def enqueue(self, payload):
        job = RemediationJob(
            repository=payload.repository,
            installation_id=payload.installation_id,
            delivery_id=payload.delivery_id,
            finding=payload.finding,
        )
        self.queue.enqueue(job)
        return job
