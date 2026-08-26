# Startup recovery

Workers now reconcile stale dispatch state before accepting new work.

Startup order:

1. Run state-aware recovery reconciliation.
2. Record the recovery report.
3. Mark startup recovery complete.
4. Start the worker polling lifecycle.

If startup recovery fails, the worker does not proceed to normal polling.

This closes the restart window where a newly started worker could begin
processing fresh jobs before stale dispatches from a previous process had been
reconciled.
