# Job system

The remediation job is a durable state machine.

```text
CREATED → QUEUED → CLONING → SCANNING → ANALYZING → PATCHING → VERIFYING
                                                                  │
                                                    ┌─────────────┴────────────┐
                                                    ▼                          ▼
                                                 VERIFIED                    FAILED
                                                    │
                                                    ▼
                                                PR_CREATED
```

## Idempotency

`X-GitHub-Delivery` is unique in PostgreSQL. Replayed webhook deliveries resolve
to the existing job instead of creating duplicate remediation runs.

## Recovery

Workers must persist state before beginning each stage. On process restart,
jobs can be selected by state and attempt count and resumed/retried according
to the worker policy.

## PostgreSQL

`remediation_jobs` stores the current state. `job_events` is append-only audit
history for every state transition.

The current repository includes an in-memory implementation for deterministic
tests. The production service should use PostgreSQL through SQLAlchemy.
