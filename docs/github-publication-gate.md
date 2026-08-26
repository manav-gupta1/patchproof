# GitHub publication gate

Required order:

sandbox execution -> authoritative evidence -> persisted evidence ->
VERIFIED -> GitHub publisher -> idempotent PR -> PR_CREATED.

The publisher rejects non-VERIFIED jobs and VERIFIED jobs without durable
evidence. PR creation is idempotent using head, base, and evidence SHA-256.
