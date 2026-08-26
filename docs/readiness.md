# Worker readiness

A deterministic readiness probe now sits in front of the worker lifecycle.

The worker reports ready only when:

1. startup recovery has completed,
2. the worker polling loop is running, and
3. the worker is not draining.

During startup, shutdown, or recovery gaps, readiness is false with a
machine-readable reason. This gives process orchestration a safe signal for
whether the instance should receive new traffic/work.
