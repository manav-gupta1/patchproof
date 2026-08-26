from __future__ import annotations
from dataclasses import dataclass
import queue
import time


@dataclass(frozen=True)
class JobLease:
    job_id: str
    owner: str
    expires_at: float


class JobQueue:
    """Local queue model for Redis/SQS semantics: enqueue + bounded leasing."""
    def __init__(self):
        self.q = queue.Queue()

    def enqueue(self, job_id):
        self.q.put(job_id)

    def claim(self, owner, ttl=30):
        job_id = self.q.get_nowait()
        return JobLease(job_id, owner, time.time() + ttl)
