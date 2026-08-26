# End-to-end worker orchestration

The SQL-backed lease now wraps the actual pipeline:

`QUEUED -> RUNNING -> verification -> authoritative evidence -> VERIFIED -> publication -> SUCCEEDED`

The worker must first acquire the SQL lease. Only the lease owner may execute
the verification and publication stages.

Verification remains the source of authoritative evidence. Publication remains
independently gated on `VERIFIED` and durable evidence.

On failure, ownership is released and the error is persisted. A second worker
cannot execute a live leased job.
