# Concurrency hardening

The retry handoff now has adversarial tests for competing workers and stale
ownership.

The tests establish these invariants:

- two workers racing for one queued retry produce exactly one successful claim;
- a stale worker cannot complete a retry after recovery has requeued it;
- a second worker cannot take ownership while the original lease is active;
- after lease expiry and reconciliation, a new worker can claim the retry.

These tests exercise the real SQL handoff and recovery components rather than
mocking the ownership transition.
