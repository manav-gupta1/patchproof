# MVP test boundary

The active MVP gate is limited to tests that exercise the current job,
persistence, lease, heartbeat, terminal-state, recovery, and lifecycle
implementation.

Historical tests remain preserved under `tests/historical/`. Other snapshot
or fixture-oriented tests are not silently treated as evidence for the
current MVP until their API ownership is reconciled.
