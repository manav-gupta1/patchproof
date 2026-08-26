# Full production-store lifecycle race

The reliability suite now combines the production store operations in one
contention scenario:

claim -> heartbeat -> success/failure

Multiple workers contend for the same set of jobs. Each job must reach
exactly one terminal state.

A second scenario covers lease expiry, recovery, reclaim by a new worker,
and final completion.

This is the broadest production-store race test so far and connects the
individual ownership, heartbeat, terminal-state, and recovery invariants.
