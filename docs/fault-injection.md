# Fault injection under contention

The worker protocol is now tested with deterministic failures injected
after job claim.

Workers can disappear before completion, causing their leases to expire.
Recovery then returns abandoned work to the queue.

The tests verify:

- expired in-flight jobs are recovered;
- stale workers cannot complete after recovery;
- a replacement worker can complete recovered work;
- injected failures do not create duplicate successful results;
- no expired job remains stuck in `running`.

The fault schedule uses deterministic random seeds so failures are
reproducible rather than flaky.
