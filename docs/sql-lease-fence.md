# SQL lease fence

Lease renewal is now enforced at the database boundary.

A heartbeat succeeds only when one conditional SQL update can prove all of:

- the job is still running;
- the worker is still the recorded owner;
- the existing lease has not expired.

An expired or stale worker therefore cannot resurrect ownership.

The same ownership/lease predicates are exposed for the result-commit path,
so result publication can require a live lease rather than trusting an
earlier in-memory claim.
