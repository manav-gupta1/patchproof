# Recovery observability

Recovery now has explicit metrics for scheduler/reconciler health:

- reconciliation runs
- retries recovered
- completed retries finalized
- reconciliation failures
- duration of the most recent run

Metrics updates are lock-protected so scheduler execution and monitoring can
safely read the same counters. Recovery failures are recorded and propagated
to the scheduler's error hook rather than being silently swallowed.
