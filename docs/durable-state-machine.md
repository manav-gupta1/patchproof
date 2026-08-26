# Durable remediation state machine

The remediation workflow now has an explicit, validated state graph:

```text
queued
  ↓
scanning
  ↓
analyzing
  ↓
patching
  ↓
verifying
  ↓
verified
  ↓
pr_created
```

Any non-terminal stage may fail into `failed`. Terminal states cannot transition
back into the workflow.

When a PostgreSQL-backed `DurableJobState` is supplied, each transition:

1. locks the job row;
2. validates the transition;
3. updates the current state;
4. appends a `job_events` record;
5. commits those changes in one transaction.

This prevents the database state and audit trail from diverging during normal
transitions.
