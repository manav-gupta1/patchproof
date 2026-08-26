from __future__ import annotations

from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from sqlalchemy import and_, update


class LeaseLost(RuntimeError):
    pass


@dataclass(frozen=True)
class LeaseRenewal:
    job_id: str
    worker_id: str
    expires_at: datetime


class SQLLeaseFence:
    """Database-enforced ownership/lease boundary for worker heartbeats."""

    def __init__(self, engine, jobs_table):
        self.engine = engine
        self.jobs_table = jobs_table

    def renew(self, job_id, worker_id, now, extension_seconds):
        new_expiry = now + timedelta(seconds=extension_seconds)
        with self.engine.begin() as conn:
            stmt = (
                update(self.jobs_table)
                .where(and_(
                    self.jobs_table.c.job_id == job_id,
                    self.jobs_table.c.status == "running",
                    self.jobs_table.c.worker_id == worker_id,
                    self.jobs_table.c.lease_until > now,
                ))
                .values(lease_until=new_expiry)
            )
            if conn.execute(stmt).rowcount != 1:
                raise LeaseLost(f"worker {worker_id!r} no longer owns {job_id!r}")
        return LeaseRenewal(job_id, worker_id, new_expiry)

    def can_commit(self, job_id, worker_id, now):
        with self.engine.connect() as conn:
            row = conn.execute(
                self.jobs_table.select().where(
                    and_(
                        self.jobs_table.c.job_id == job_id,
                        self.jobs_table.c.status == "running",
                        self.jobs_table.c.worker_id == worker_id,
                        self.jobs_table.c.lease_until > now,
                    )
                )
            ).first()
        return row is not None
