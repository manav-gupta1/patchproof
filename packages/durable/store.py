from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass


@dataclass(frozen=True)
class JobEvent:
    job_id: str
    from_state: str
    to_state: str
    attempt: int
    error: str | None = None


class DurableJobStore:
    """
    SQLite reference implementation of the production persistence contract.

    PostgreSQL is the deployment database; this adapter makes transaction,
    uniqueness, and recovery semantics executable without external services.
    """
    def __init__(self, path=":memory:"):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                state TEXT NOT NULL,
                attempt INTEGER NOT NULL DEFAULT 0,
                lease_owner TEXT,
                lease_until REAL,
                error TEXT,
                version INTEGER NOT NULL DEFAULT 0
            )
        """)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS job_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                from_state TEXT NOT NULL,
                to_state TEXT NOT NULL,
                attempt INTEGER NOT NULL,
                error TEXT
            )
        """)
        self.db.commit()
        self.lock = threading.RLock()

    def create(self, job_id: str, state="RECEIVED"):
        with self.lock, self.db:
            self.db.execute(
                "INSERT OR IGNORE INTO jobs(job_id,state) VALUES(?,?)",
                (job_id, state),
            )

    def get(self, job_id: str):
        row = self.db.execute(
            "SELECT job_id,state,attempt,lease_owner,lease_until,error,version "
            "FROM jobs WHERE job_id=?", (job_id,)
        ).fetchone()
        return row

    def transition(self, job_id, expected_state, new_state, *,
                  attempt=None, error=None):
        with self.lock, self.db:
            row = self.db.execute(
                "SELECT state,attempt,version FROM jobs WHERE job_id=?",
                (job_id,),
            ).fetchone()
            if not row:
                raise KeyError(job_id)
            current, current_attempt, version = row
            if current != expected_state:
                raise ValueError(f"stale transition: {current} != {expected_state}")
            next_attempt = current_attempt if attempt is None else attempt
            updated = self.db.execute(
                """UPDATE jobs SET state=?, attempt=?, error=?, version=version+1
                   WHERE job_id=? AND state=? AND version=?""",
                (new_state, next_attempt, error, job_id, expected_state, version),
            ).rowcount
            if updated != 1:
                raise RuntimeError("optimistic concurrency conflict")
            self.db.execute(
                """INSERT INTO job_events(job_id,from_state,to_state,attempt,error)
                   VALUES(?,?,?,?,?)""",
                (job_id, current, new_state, next_attempt, error),
            )

    def acquire_lease(self, job_id, owner, now=None, ttl=None, *, ttl_seconds=None):
        if ttl is None:
            ttl = ttl_seconds
        if ttl is None:
            raise TypeError("acquire_lease requires ttl or ttl_seconds")
        if now is None:
            import time
            now = time.time()
        if hasattr(ttl, "total_seconds"):
            ttl = ttl.total_seconds()
        with self.lock, self.db:
            row = self.db.execute(
                "SELECT lease_owner,lease_until FROM jobs WHERE job_id=?",
                (job_id,),
            ).fetchone()
            if not row:
                raise KeyError(job_id)
            current_owner, lease_until = row
            if current_owner and lease_until and lease_until > now and current_owner != owner:
                return False
            updated = self.db.execute(
                """UPDATE jobs SET lease_owner=?, lease_until=?, version=version+1
                   WHERE job_id=?""",
                (owner, now + ttl, job_id),
            ).rowcount
            return updated == 1

    def release_lease(self, job_id, owner):
        with self.lock, self.db:
            self.db.execute(
                """UPDATE jobs SET lease_owner=NULL, lease_until=NULL, version=version+1
                   WHERE job_id=? AND lease_owner=?""",
                (job_id, owner),
            )

    def events(self, job_id):
        return self.db.execute(
            "SELECT job_id,from_state,to_state,attempt,error "
            "FROM job_events WHERE job_id=? ORDER BY id",
            (job_id,),
        ).fetchall()
