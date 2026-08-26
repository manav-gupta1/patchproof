# Lease timing race

The lease boundary is now explicitly tested for the three critical operations:

- renewal before expiry extends the ownership window;
- renewal after expiry cannot resurrect ownership;
- result commit after expiry is rejected.

The concurrent renewal/commit test also verifies that completion is terminal:
once a result is committed, a later heartbeat cannot revive the lease.

The production SQL implementation should preserve these same invariants by
making renewal and completion conditional on current ownership and lease
validity.
