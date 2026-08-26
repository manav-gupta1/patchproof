# Heartbeat vs terminal-state races

Heartbeats are now tested against terminal transitions.

Once a job reaches `SUCCEEDED` or `FAILED`, a later heartbeat from the old
worker is rejected. Concurrent heartbeat/terminal attempts are also tested
so a heartbeat cannot revive, extend, or otherwise mutate terminal state.

The tests cover both success and failure terminal paths.
