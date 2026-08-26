from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import and_, select, update


class RecoveryReconciler:
    """Reconcile expired retry dispatches with authoritative job state."""

    def __init__(self, engine, retry_table, job_table):
        self.engine = engine
        self.retry_table = retry_table
        self.job_table = job_table

    def reconcile(self, now=None):
        now = now or datetime.now(timezone.utc)
        recovered = []
        completed = []

        with self.engine.begin() as conn:
            rows = conn.execute(
                select(self.retry_table)
                .where(
                    (self.retry_table.c.state == "dispatched")
                    & (self.retry_table.c.dispatch_until <= now)
                )
            ).mappings().all()

            for retry in rows:
                job = conn.execute(
                    select(self.job_table)
                    .where(self.job_table.c.job_id == retry["job_id"])
                ).mappings().first()

                if job is None:
                    # Keep the retry record: the job may be restored by a
                    # separate repair workflow.
                    continue

                if job["status"] == "succeeded":
                    conn.execute(
                        self.retry_table.delete().where(
                            self.retry_table.c.job_id == retry["job_id"]
                        )
                    )
                    completed.append(retry["job_id"])
                    continue

                # If the job is no longer owned by the dispatch owner, the
                # handoff did not remain active; make the retry runnable again.
                # Release the durable job lease held by the crashed worker.
                # Otherwise a recovered retry is queued but no replacement
                # worker can acquire the job.
                conn.execute(
                    update(self.job_table)
                    .where(self.job_table.c.job_id == retry["job_id"])
                    .values(
                        status="queued",
                        lease_owner=None,
                        lease_until=None,
                    )
                )

                conn.execute(
                    update(self.retry_table)
                    .where(and_(
                        self.retry_table.c.job_id == retry["job_id"],
                        self.retry_table.c.state == "dispatched",
                    ))
                    .values(
                        state="queued",
                        dispatch_owner=None,
                        dispatch_until=None,
                        next_run_at=datetime.now(timezone.utc),
                    )
                )
                recovered.append(retry["job_id"])

        return {"recovered": recovered, "completed": completed}
