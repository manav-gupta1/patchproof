# SQL result fence

The stale-result protection is now enforced at the database boundary.

A successful result is committed with a single conditional `UPDATE` that
requires both:

- the job is still `running`; and
- the committing worker is still the recorded owner.

If the conditional update affects zero rows, the worker is stale (or the job
was already completed), and the result is rejected.

This makes result fencing an SQL invariant rather than an application-only
check.
