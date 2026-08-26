# Durable publication recovery

Publication transaction records are now persisted in SQL.

A worker restart does not lose the `BRANCH_PUSHED` checkpoint. Recovery loads
the record, verifies that the evidence SHA-256 still matches, and resumes PR
creation without re-pushing the branch.

`PR_CREATED` is also persisted, so replay after a completed publication is a
read-only/idempotent operation.

The transaction is therefore durable across process restarts, not merely
crash-safe within one process.
