# Multi-worker stress

The reliability protocol is now exercised under repeated multi-worker
contention.

The stress tests use eight concurrent workers over 100 jobs and repeat a
six-worker contention run ten times.

Invariants checked:

- every queued job is completed exactly once;
- no job is claimed by two workers simultaneously;
- all jobs eventually reach `succeeded`;
- repeated contention does not create duplicate completions.

This is a concurrency stress layer above the targeted lease and stale-result
race tests.
