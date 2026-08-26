from __future__ import annotations
import os
from contextlib import contextmanager
try:
    import psycopg
except ImportError:
    psycopg = None

class Database:
    def __init__(self, dsn=None):
        self.dsn = dsn or os.environ.get("POSTGRES_DSN","postgresql://patchproof:patchproof@localhost:5432/patchproof")
        if psycopg is None:
            raise RuntimeError("psycopg is required for PostgreSQL persistence")
    @contextmanager
    def connection(self):
        with psycopg.connect(self.dsn) as conn:
            yield conn
