from __future__ import annotations

from packages.queue.models import RemediationTask


class QueueBackend:
    def enqueue(self, task: RemediationTask) -> str:
        raise NotImplementedError

    def dequeue(self) -> RemediationTask | None:
        raise NotImplementedError
