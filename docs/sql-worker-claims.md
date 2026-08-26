# SQL-backed worker claims

Worker ownership is now enforced by the database rather than process memory.

`claim()` uses one conditional SQL `UPDATE`. The update succeeds only when the
job has no live lease or its previous lease has expired. The affected-row count
is the ownership decision.

Completion operations are also owner-fenced: a worker can only heartbeat,
succeed, or fail while it still owns the current lease.

This is the production concurrency contract needed for multiple worker
processes/containers sharing the same database.
