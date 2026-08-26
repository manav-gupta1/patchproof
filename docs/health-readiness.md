# Health and readiness probes

The worker now exposes separate liveness and readiness semantics.

**Health/liveness** answers: is the process alive and its polling lifecycle
running?

**Readiness** answers: should this instance receive new work?

A draining worker can therefore remain healthy while becoming not-ready.
This prevents orchestrators from killing a healthy instance merely because it
is performing a graceful shutdown.
