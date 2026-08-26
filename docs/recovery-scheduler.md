# Recovery scheduler

The recovery reconciler is now continuously scheduled by a bounded background
loop.

Each iteration delegates to the state-aware reconciler. The reconciler remains
the source of truth: it checks expired dispatches against authoritative job
state before requeueing or finalizing them.

The scheduler can be started and stopped cleanly and supports an optional
result callback for metrics/logging.
