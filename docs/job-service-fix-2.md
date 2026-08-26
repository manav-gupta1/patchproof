# Job service contract hardening

Added two concrete service-layer fixes:

- JobRecord self-transitions are treated as idempotent no-ops.
- InMemoryJobStore returns the existing job for duplicate job IDs/delivery IDs,
  matching the JobService's webhook idempotency contract.

The historical CLONING state remains intentionally absent from the current
state machine.
