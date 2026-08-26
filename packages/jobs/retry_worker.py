from __future__ import annotations

from packages.jobs.retry_policy import RetryPolicy


class RetryingWorker:
    def __init__(self, worker, retry_policy, retry_store):
        self.worker = worker
        self.retry_policy = retry_policy
        self.retry_store = retry_store

    def run(self, *, job, attempt, **kwargs):
        try:
            return self.worker.run(job=job, **kwargs)
        except Exception as exc:
            decision = self.retry_policy.decide(exc, attempt)
            if decision.retry:
                self.retry_store.record_retry(
                    job.job_id, attempt + 1,
                    decision.delay_seconds, decision.reason,
                )
            return decision
