# Live-lease failure

The production `SQLJobStore.fail()` path now uses the same live-lease
invariant as `succeed()`.

A worker can transition a job to `FAILED` only while it is still RUNNING,
remains the current lease owner, has a lease, and the lease is still valid
at the supplied time.

The ownership/lease predicates and terminal transition are part of one
conditional SQL update, preventing an expired or reclaimed worker from
publishing a stale failure.
