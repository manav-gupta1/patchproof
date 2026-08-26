# Durable runtime contract

## Production topology

FastAPI -> PostgreSQL -> Redis -> worker -> isolated verification sandbox.

PostgreSQL is the source of truth for job state and audit events.
Redis is transport/lease infrastructure, not the authoritative state store.

## Guarantees

- job IDs are unique
- state transitions are optimistic-concurrency checked
- every transition is append-audited
- worker execution uses leases
- expired leases can be reclaimed
- failed work remains observable instead of disappearing
- promotion still requires VERIFIED

## Production mapping

| Reference adapter | Production |
|---|---|
| SQLite `DurableJobStore` | PostgreSQL + SQLAlchemy |
| `JobQueue` | Redis Streams / consumer groups |
| local lease | Redis lease + DB ownership/version |
| Worker | Celery or dedicated asyncio worker |
| process-local memory | PostgreSQL |
