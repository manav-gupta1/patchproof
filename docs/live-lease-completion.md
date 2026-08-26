# Live-lease completion

The production `SQLJobStore.succeed()` path now enforces the complete
completion invariant in its conditional SQL update.

A worker can transition a job to `SUCCEEDED` only when:

- the job is `RUNNING`;
- the worker is the current lease owner;
- a lease exists; and
- the lease has not expired at the supplied `now`.

The check and state transition occur in the same database operation, so an
expired or reclaimed worker cannot complete the job after losing its lease.

The existing API remains compatible for callers that omit `now`; the
method uses the current UTC time in that case.
