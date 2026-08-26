# Concurrent result race

The SQL result fence is now exercised with two threads attempting to commit
the same job concurrently.

The test verifies that the conditional database update provides a single
winner and rejects the losing/stale commit. It also verifies that once a job
has reached `succeeded`, later concurrent commits cannot replace the
authoritative result.

This is the database-level contention test for the stale-result invariant.
