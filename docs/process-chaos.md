# Process-level chaos integration

The reliability suite now crosses the process boundary.

Worker subprocesses are intentionally terminated at two critical points:

- immediately after claim;
- immediately after heartbeat.

The tests verify that these are real non-zero process exits, that durable
state written before termination survives, and that a fresh process can
start afterward and continue the workflow.

This is a process-level complement to the in-process lease and concurrency
tests. It deliberately keeps the crash points deterministic so failures
remain reproducible in CI.
