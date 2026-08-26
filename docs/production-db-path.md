# Production database path

The next validation layer explicitly targets the repository's
`SQLJobStore`, rather than a separate chaos-test schema.

The checks ensure the production store is the object under test and that
its real schema initialization path is usable.

The remaining integration work is to expose the production store's
claim, lease-renewal, recovery, and atomic-completion operations through
one process-level scenario. This avoids claiming parity merely because a
parallel test harness passes.
