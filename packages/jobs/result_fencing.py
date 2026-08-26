from __future__ import annotations


class StaleResultRejected(RuntimeError):
    pass


class ResultFence:
    """Require current job ownership before committing a worker result."""

    def __init__(self, job_store):
        self.job_store = job_store

    def commit(self, job_id, worker_id, result):
        # The job store must atomically verify ownership and completion.
        if not self.job_store.succeed(job_id, worker_id, result):
            raise StaleResultRejected(
                f"worker {worker_id!r} no longer owns job {job_id!r}"
            )
        return result
