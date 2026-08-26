from __future__ import annotations

from dataclasses import dataclass
from sqlalchemy import and_, update
import threading


class StaleResultRejected(RuntimeError):
    """The worker no longer owns the job at commit time."""


@dataclass(frozen=True)
class ResultCommit:
    job_id: str
    worker_id: str
    result: object


class SQLResultFence:
    """Database-backed result fence using one conditional UPDATE."""

    def __init__(self, engine, jobs_table):
        self.engine = engine
        self.jobs_table = jobs_table
        self._lock = threading.RLock()

    def commit(self, job_id, worker_id, result):
        # SQLite serializes writers at the database level; serialize commits
        # in-process so a losing race deterministically observes rowcount=0
        # rather than surfacing an OperationalError from the SQLite lock.
        with self._lock, self.engine.begin() as conn:
            stmt = (
                update(self.jobs_table)
                .where(
                    and_(
                        self.jobs_table.c.job_id == job_id,
                        self.jobs_table.c.status == "running",
                        self.jobs_table.c.worker_id == worker_id,
                    )
                )
                .values(
                    status="succeeded",
                    result=result,
                    worker_id=None,
                )
            )
            outcome = conn.execute(stmt)

            if outcome.rowcount != 1:
                raise StaleResultRejected(
                    f"worker {worker_id!r} no longer owns job {job_id!r}"
                )

        return ResultCommit(job_id, worker_id, result)
