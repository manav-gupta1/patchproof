# End-to-end crash/restart scenario

The worker reliability protocol is now tested as one lifecycle:

1. runtime starts;
2. worker claims a queued job;
3. process disappears without graceful completion;
4. a new runtime starts;
5. startup recovery requeues the expired job;
6. a new worker claims it;
7. the new owner completes it;
8. the old worker is unable to publish a stale result.

This test joins the previously isolated lifecycle, lease, recovery and
completion invariants into a single restart scenario.
