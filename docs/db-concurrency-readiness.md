# Database concurrency readiness

The race suite now includes a portability/readiness gate around the real
`SQLJobStore`.

The gate verifies that production operations run through SQLAlchemy
transactions and that the real store creates its schema through the
production path.

SQLite remains useful for deterministic unit/concurrency tests, but it is
not treated as proof of production row-locking semantics. A live
production-engine integration requires credentials/environment for that
database and is intentionally not fabricated here.
