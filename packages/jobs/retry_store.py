from __future__ import annotations
from datetime import datetime, timedelta, timezone
from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, select

def _share_sqlite_memory_engine(engine):
    if engine.url.get_backend_name() == "sqlite" and engine.url.database in (None, ""):
        from sqlalchemy.pool import StaticPool
        if not isinstance(engine.pool, StaticPool):
            dbapi = engine.dialect.dbapi
            engine.pool = StaticPool(
                creator=lambda: dbapi.connect(":memory:", check_same_thread=False)
            )
    return engine


def _utc(value):
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class SQLRetryStore:
    def __init__(self, engine):
        self.engine = _share_sqlite_memory_engine(engine)
        self.metadata = MetaData()
        self.jobs = Table(
            "job_retries", self.metadata,
            Column("job_id", String(255), primary_key=True),
            Column("attempts", Integer, nullable=False, default=0),
            Column("next_run_at", DateTime(timezone=True), nullable=False),
            Column("last_error", String(2000), nullable=True),
            Column("state", String(32), nullable=False, default="queued"),
            Column("dispatch_owner", String(255), nullable=True),
            Column("dispatch_until", DateTime(timezone=True), nullable=True),
        )

    def create_schema(self):
        self.metadata.create_all(self.engine)

    def record_retry(self, job_id, attempt, delay_seconds, error):
        when = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
        with self.engine.begin() as conn:
            row = conn.execute(select(self.jobs.c.job_id).where(self.jobs.c.job_id == job_id)).first()
            values = dict(attempts=attempt, next_run_at=when,
                          last_error=str(error)[:2000], state="queued",
                          dispatch_owner=None, dispatch_until=None)
            if row:
                conn.execute(self.jobs.update().where(self.jobs.c.job_id == job_id).values(**values))
            else:
                conn.execute(self.jobs.insert().values(job_id=job_id, **values))

    def get(self, job_id):
        with self.engine.begin() as conn:
            row = conn.execute(select(self.jobs).where(self.jobs.c.job_id == job_id)).mappings().first()
            if row is None:
                return None
            value = dict(row)
            value["next_run_at"] = _utc(value.get("next_run_at"))
            if value.get("dispatch_until") is not None:
                value["dispatch_until"] = _utc(value["dispatch_until"])
            return value

    def due(self, now=None):
        now = _utc(now) if now is not None else datetime.now(timezone.utc)
        with self.engine.begin() as conn:
            rows = list(conn.execute(select(self.jobs).where(
                (self.jobs.c.next_run_at <= now) & (self.jobs.c.state == "queued")
            )).mappings())
            return [dict(r, next_run_at=_utc(r["next_run_at"])) for r in rows]
