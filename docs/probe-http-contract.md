# Probe HTTP contract

The health/readiness semantics now have a framework-neutral HTTP adapter.

- Health returns HTTP 200 while the process lifecycle is running.
- Health returns HTTP 503 when the lifecycle is stopped.
- Readiness returns HTTP 200 only when the worker is ready.
- Readiness returns HTTP 503 during startup recovery or graceful drain.
- Responses use JSON and include machine-readable readiness reasons.

A web framework can mount these methods at its preferred `/health` and
`/ready` endpoints without changing the underlying worker state model.
