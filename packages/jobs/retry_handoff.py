from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import threading

from sqlalchemy import and_, select, update


class RetryHandoff:
    def __init__(self, engine, retry_table, job_table):
        self.engine = engine
        self.retry_table = retry_table
        self.job_table = job_table
        self._lock = threading.RLock()
        self._shared_connection = (
            engine.connect()
            if engine.dialect.name == "sqlite" and not engine.url.database
            else None
        )

    @contextmanager
    def _transaction(self):
        if self._shared_connection is not None:
            tx = self._shared_connection.begin()
            try:
                yield self._shared_connection
                tx.commit()
            except Exception:
                tx.rollback()
                raise
        else:
            with self.engine.begin() as conn:
                yield conn

    def claim(self, job_id, worker_id, lease_seconds=60, now=None):
        now = now or datetime.now(timezone.utc)
        until = now + timedelta(seconds=lease_seconds)
        with self._lock, self._transaction() as conn:
            retry = conn.execute(select(self.retry_table).where(and_(
                self.retry_table.c.job_id == job_id,
                self.retry_table.c.next_run_at <= now,
                self.retry_table.c.state == "queued",
            ))).mappings().first()
            if retry is None:
                return None

            result = conn.execute(update(self.job_table).where(and_(
                self.job_table.c.job_id == job_id,
                self.job_table.c.status != "succeeded",
                (self.job_table.c.lease_owner.is_(None) |
                 self.job_table.c.lease_until.is_(None) |
                 (self.job_table.c.lease_until <= now)),
            )).values(
                status="running",
                attempts=self.job_table.c.attempts + 1,
                lease_owner=worker_id,
                lease_until=until,
                last_error=None,
            ))
            if result.rowcount != 1:
                return None

            changed = conn.execute(update(self.retry_table).where(and_(
                self.retry_table.c.job_id == job_id,
                self.retry_table.c.state == "queued",
            )).values(
                state="dispatched",
                dispatch_owner=worker_id,
                dispatch_until=until,
            ))
            if changed.rowcount != 1:
                raise RuntimeError("retry state changed during handoff")


            return {
                "job_id": job_id,
                "attempt": retry["attempts"],
                "lease_until": until,
            }

    def release_failed_execution(self, job_id, worker_id):
        """Release the job lease after a transient worker failure.

        The retry row remains DISPATCHED until the retry policy records the
        next queued attempt, so failure cannot cause a duplicate execution.
        """
        with self._lock, self._transaction() as conn:
            conn.execute(update(self.job_table).where(and_(
                self.job_table.c.job_id == job_id,
                self.job_table.c.lease_owner == worker_id,
            )).values(
                status="queued",
                lease_owner=None,
                lease_until=None,
            ))

    def complete(self, job_id, worker_id):
        with self._lock, self._transaction() as conn:
            result = conn.execute(self.retry_table.delete().where(and_(
                self.retry_table.c.job_id == job_id,
                self.retry_table.c.state == "dispatched",
                self.retry_table.c.dispatch_owner == worker_id,
            )))
            if result.rowcount == 1:
                conn.execute(update(self.job_table).where(
                    self.job_table.c.job_id == job_id
                ).values(lease_owner=None, lease_until=None))
            return result.rowcount == 1

    def recover_expired(self, now=None):
        now = now or datetime.now(timezone.utc)
        with self._lock, self._transaction() as conn:
            result = conn.execute(update(self.retry_table).where(and_(
                self.retry_table.c.state == "dispatched",
                self.retry_table.c.dispatch_until <= now,
            )).values(
                state="queued", dispatch_owner=None,
                dispatch_until=None, next_run_at=now,
            ))
            return result.rowcount
