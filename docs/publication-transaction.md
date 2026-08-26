# Crash-safe publication transaction

Publication phases are:

`READY -> BRANCH_PUSHED -> PR_CREATED`

The already-reviewed patch is pushed first. The `BRANCH_PUSHED` record, including
commit SHA and evidence SHA-256, is persisted before PR creation.

If a worker crashes after the push, a retry resumes from `BRANCH_PUSHED` and does
not push the patch again.

A transaction cannot resume with different evidence for the same job.
