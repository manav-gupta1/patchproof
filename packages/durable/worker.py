from __future__ import annotations
import time


class Worker:
    def __init__(self, store, queue, orchestrator, worker_id):
        self.store = store
        self.queue = queue
        self.orchestrator = orchestrator
        self.worker_id = worker_id

    def run_once(self):
        lease = self.queue.claim(self.worker_id)
        try:
            job = self.store.get(lease.job_id)
            if not job:
                raise KeyError(lease.job_id)
            # Actual orchestration is delegated to the existing service.
            return self.orchestrator(lease.job_id)
        finally:
            self.store.release_lease(lease.job_id, self.worker_id)
