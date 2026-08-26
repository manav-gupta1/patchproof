from __future__ import annotations

from dataclasses import dataclass
from sqlalchemy import and_, update


class CompletionRejected(RuntimeError):
    """The worker cannot complete because ownership/lease is no longer valid."""


@dataclass(frozen=True)
class Completion:
    job_id: str
    worker_id: str
    result: object


class SQLCompletion:
    """Atomically verify live ownership and complete a running job."""

    def __init__(self, engine, jobs_table):
        self.engine = engine
        self.jobs_table = jobs_table

    def commit(self, job_id, worker_id, now, result):
        with self.engine.begin() as conn:
            stmt = (
                update(self.jobs_table)
                .where(and_(
                    self.jobs_table.c.job_id == job_id,
                    self.jobs_table.c.status == "running",
                    self.jobs_table.c.worker_id == worker_id,
                    self.jobs_table.c.lease_until > now,
                ))
                .values(
                    status="succeeded",
                    result=result,
                    worker_id=None,
                )
            )
            if conn.execute(stmt).rowcount != 1:
                raise CompletionRejected(
                    f"completion rejected for worker {worker_id!r} on {job_id!r}"
                )
        return Completion(job_id, worker_id, result)
