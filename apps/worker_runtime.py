from __future__ import annotations

import os
import socket

from packages.durable.store import DurableJobStore
from packages.queue.redis_stream import RedisStreamQueue


class WorkerRuntime:
    """
    Production wiring boundary.

    Network clients, LLM providers, repository checkout, and sandbox runner
    are injected into the remediation orchestrator rather than hidden here.
    """
    def __init__(self, store, queue, orchestrator, worker_id=None):
        self.store = store
        self.queue = queue
        self.orchestrator = orchestrator
        self.worker_id = worker_id or socket.gethostname()

    def process(self, job_id):
        if not self.store.acquire_lease(job_id, self.worker_id, ttl_seconds=300):
            return {"status": "already_claimed", "job_id": job_id}
        try:
            result = self.orchestrator(job_id)
            return {"status": "processed", "job_id": job_id, "result": result}
        except Exception as exc:
            return {"status": "failed", "job_id": job_id, "error": str(exc)}
        finally:
            self.store.release_lease(job_id, self.worker_id)

    def run_once(self, count=1):
        messages = self.queue.read(self.worker_id, count=count)
        processed = []
        for _, entries in messages:
            for message_id, values in entries:
                job_id = values[b"job_id"].decode() if isinstance(values[b"job_id"], bytes) else values["job_id"]
                result = self.process(job_id)
                if result["status"] != "already_claimed":
                    self.queue.ack(message_id)
                processed.append(result)
        return processed
