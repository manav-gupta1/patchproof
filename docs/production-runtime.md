# Production runtime composition

The reliability components are now composed behind a single production
runtime boundary.

Startup ordering is enforced as:

1. startup recovery
2. worker lifecycle start
3. readiness becomes true

Shutdown delegates through the same graceful worker lifecycle.

Health/readiness probes are created from the same runtime-owned state, reducing
the risk that deployment probes observe a different lifecycle than the worker
actually uses.
