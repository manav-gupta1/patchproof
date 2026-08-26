from datetime import datetime, timezone
from uuid import uuid4

from packages.jobs.postgres import PostgresJobStore


class FakeCursor:
    def __init__(self, rows):
        self.rows = iter(rows)
        self.last = None
        self.rowcount = 1

    def execute(self, sql, params=None):
        self.last = sql
        if "INSERT INTO job_idempotency_keys" in sql:
            self._current = next(self.rows, None)

    def fetchone(self):
        return getattr(self, "_current", None)


class FakeConn:
    def __init__(self, rows):
        self.cursor_obj = FakeCursor(rows)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        pass


def test_schema_contains_transactional_primitives():
    from pathlib import Path
    schema = Path("packages/jobs/schema.sql").read_text()
    assert "FOR UPDATE SKIP LOCKED" in Path("packages/jobs/postgres.py").read_text()
    assert "lease_expires_at" in schema
    assert "job_idempotency_keys" in schema
    assert "job_events" in schema
