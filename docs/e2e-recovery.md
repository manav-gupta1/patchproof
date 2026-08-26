# End-to-end recovery validation

The integration suite now exercises the complete durable recovery path:

1. A retry is queued.
2. A worker claims it and crashes before execution.
3. The dispatch lease expires.
4. The recovery reconciler requeues the retry.
5. A second worker executes it and encounters a transient failure.
6. A new retry attempt is persisted.
7. A later worker executes the retry successfully.
8. The retry record is finalized.

The same scenario also validates recovery metrics.

This test is intentionally state-driven and uses the real SQL stores,
handoff, dispatcher, reconciler, and observability components together.
