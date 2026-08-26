# Production worker lifecycle

The worker now has an explicit lifecycle controller.

- `start()` begins polling.
- `drain()` stops accepting new work while allowing in-flight work to finish.
- `stop()` drains, waits for idle work, then terminates the polling loop.
- Poll errors are surfaced through an error callback without silently killing
  the worker loop.

This provides a clean boundary for process termination and deployment
shutdowns while preserving the existing lease/heartbeat/recovery guarantees.
