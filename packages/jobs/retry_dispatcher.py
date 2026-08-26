from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from packages.jobs.retry_handoff import RetryHandoff


class RetryDispatcher:
    """Dispatch due retries through the same atomic lease/handoff boundary."""

    def __init__(self, retries, jobs, worker=None, job_loader=None):
        if isinstance(retries, RetryHandoff):
            # Legacy atomic-handoff injection:
            # RetryDispatcher(handoff, Worker(), loader)
            self.handoff = retries
            self.retries = None
            self.jobs = None
            self.worker = jobs
            self.job_loader = worker
        else:
            self.retries = retries
            self.jobs = jobs
            self.worker = worker
            self.job_loader = job_loader
            self.handoff = RetryHandoff(
                retries.engine, retries.jobs, jobs.jobs
            )

    def dispatch_due(self, *, worker_id, limit=100, now=None):
        now = now or datetime.now(timezone.utc)
        retry_table = (
            self.retries.jobs if self.retries is not None
            else self.handoff.retry_table
        )
        with self.handoff.engine.begin() as conn:
            ids = conn.execute(
                select(retry_table.c.job_id).where(
                    (retry_table.c.state == "queued")
                    & (
                        (retry_table.c.next_run_at <= now)
                        | (self.retries is None)
                    )
                ).limit(limit)
            ).scalars().all()


        results = []
        for job_id in ids:
            handoff = self.handoff.claim(job_id, worker_id, now=now)
            if handoff is None:
                continue

            # The lightweight dispatcher contract only claims the retry when
            # no worker was supplied. This is used by scheduler/lease tests.
            if self.worker is None:
                results.append((job_id, handoff["attempt"]))
                continue

            try:
                if self.job_loader is None:
                    raise KeyError(f"no job loader for {job_id}")
                job, kwargs = self.job_loader(job_id)
                result = self.worker.run(
                    job=job, worker_id=worker_id, **kwargs
                )
                if result:
                    self.handoff.complete(job_id, worker_id)
                results.append({
                    "job_id": job_id,
                    "attempt": handoff["attempt"],
                    "status": "succeeded" if result else "not_run",
                    "result": result,
                })
            except Exception as exc:
                # The retry policy owns persistence of the next attempt. Free
                # the current job lease so that policy can safely re-queue it.
                self.handoff.release_failed_execution(job_id, worker_id)
                results.append({
                    "job_id": job_id,
                    "attempt": handoff["attempt"],
                    "status": "failed",
                    "error": str(exc),
                })
        return results
