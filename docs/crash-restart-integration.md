# Crash/restart integration

Restart recovery is now exercised as a lifecycle boundary.

The integration test models a worker disappearing while holding a live
lease, advances time past expiry, and starts recovery. Recovery requeues
the abandoned job and clears the old owner.

The test also verifies idempotence: repeating recovery does not recover the
same job twice, while a still-live worker is left untouched.

This is the bridge between the lease/result invariants and process restart
behavior.
