from collections import deque

from packages.queue.models import RemediationTask


class MemoryQueue:
    def __init__(self) -> None:
        self.items: deque[RemediationTask] = deque()

    def enqueue(self, task: RemediationTask) -> str:
        self.items.append(task)
        return task.job_id

    def dequeue(self) -> RemediationTask | None:
        return self.items.popleft() if self.items else None
