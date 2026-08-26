from __future__ import annotations

from datetime import datetime, timedelta, timezone
from sqlalchemy import (
    Column, DateTime, Integer, MetaData, String, Table, create_engine,
    select, update, and_, or_
)
from packages.jobs.worker import JobRecord, JobStatus, JobLeaseError


def _engine_for_url(engine):
    # SQLite in-memory databases are connection-local. The retry handoff and
    # recovery layers intentionally share the same engine, so all of them
    # must see the same in-memory schema/rows. Production uses Postgres and is
    # unaffected by this test/dev-only connection policy.
    if engine.url.get_backend_name() == "sqlite" and engine.url.database in (None, ""):
        from sqlalchemy.pool import StaticPool
        if not isinstance(engine.pool, StaticPool):
            database = engine.url.database or ":memory:"
            dbapi = engine.dialect.dbapi
            engine.pool = StaticPool(
                creator=lambda: dbapi.connect(database, check_same_thread=False)
            )
    return engine


class SQLJobStore:
    def __init__(self, engine):
        self.engine = _engine_for_url(engine)
        self.metadata = MetaData()
        self.jobs = Table(
            "jobs",
            self.metadata,
            Column("job_id", String(255), primary_key=True),
            Column("status", String(32), nullable=False),
            Column("attempts", Integer, nullable=False, default=0),
            Column("lease_owner", String(255), nullable=True),
            Column("lease_until", DateTime(timezone=True), nullable=True),
            Column("last_error", String(2000), nullable=True),
        )

    def create_schema(self):
        self.metadata.create_all(self.engine)

    def create(self, job_id):
        with self.engine.begin() as conn:
            conn.execute(self.jobs.insert().values(
                job_id=job_id, status=JobStatus.QUEUED.value, attempts=0
            ))
        return job_id

    def get(self, job_id):
        with self.engine.begin() as conn:
            row = conn.execute(
                select(self.jobs).where(self.jobs.c.job_id == job_id)
            ).mappings().first()
        if row is None:
            raise KeyError(job_id)
        return JobRecord(
            job_id=row["job_id"],
            status=JobStatus(row["status"]),
            attempts=row["attempts"],
            lease_owner=row["lease_owner"],
            lease_until=row["lease_until"],
            last_error=row["last_error"],
        )

    def claim(self, job_id, worker_id, lease_seconds=60, now=None):
        now = now or datetime.now(timezone.utc)
        until = now + timedelta(seconds=lease_seconds)

        # Atomic conditional UPDATE: only one concurrent claimant can satisfy
        # the predicate for a live QUEUED/expired job.
        with self.engine.begin() as conn:
            result = conn.execute(
                update(self.jobs)
                .where(
                    and_(
                        self.jobs.c.job_id == job_id,
                        or_(
                            self.jobs.c.status == JobStatus.QUEUED.value,
                            and_(
                                self.jobs.c.status == JobStatus.RUNNING.value,
                                or_(
                                    self.jobs.c.lease_owner.is_(None),
                                    self.jobs.c.lease_until.is_(None),
                                    self.jobs.c.lease_until <= now,
                                ),
                            ),
                        ),
                    )
                )
                .values(
                    status=JobStatus.RUNNING.value,
                    attempts=self.jobs.c.attempts + 1,
                    lease_owner=worker_id,
                    lease_until=until,
                    last_error=None,
                )
            )
            return result.rowcount == 1

    def heartbeat(self, job_id, worker_id, lease_seconds=60, now=None):
        now = now or datetime.now(timezone.utc)
        until = now + timedelta(seconds=lease_seconds)
        with self.engine.begin() as conn:
            result = conn.execute(
                update(self.jobs)
                .where(and_(
                    self.jobs.c.job_id == job_id,
                    self.jobs.c.status == JobStatus.RUNNING.value,
                    self.jobs.c.lease_owner == worker_id,
                    self.jobs.c.lease_until > now,
                ))
                .values(lease_until=until)
            )
            if result.rowcount != 1:
                raise JobLeaseError("worker lease is not valid")

    def succeed(self, job_id, worker_id, now=None):
        now = now or datetime.now(timezone.utc)
        with self.engine.begin() as conn:
            result = conn.execute(
                update(self.jobs)
                .where(and_(
                    self.jobs.c.job_id == job_id,
                    self.jobs.c.status == JobStatus.RUNNING.value,
                    self.jobs.c.lease_owner == worker_id,
                    self.jobs.c.lease_until.is_not(None),
                    self.jobs.c.lease_until > now,
                ))
                .values(
                    status=JobStatus.SUCCEEDED.value,
                    lease_owner=None,
                    lease_until=None,
                    last_error=None,
                )
            )
            if result.rowcount != 1:
                raise JobLeaseError("worker lease is not valid")

    def fail(self, job_id, worker_id, error, now=None):
        now = now or datetime.now(timezone.utc)
        with self.engine.begin() as conn:
            result = conn.execute(
                update(self.jobs)
                .where(and_(
                    self.jobs.c.job_id == job_id,
                    self.jobs.c.status == JobStatus.RUNNING.value,
                    self.jobs.c.lease_owner == worker_id,
                    self.jobs.c.lease_until.is_not(None),
                    self.jobs.c.lease_until > now,
                ))
                .values(
                    status=JobStatus.FAILED.value,
                    lease_owner=None,
                    lease_until=None,
                    last_error=error,
                )
            )
            if result.rowcount != 1:
                raise JobLeaseError("worker lease is not valid")
