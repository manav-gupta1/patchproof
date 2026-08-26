# Stale-result fencing

A worker result is now treated as valid only when the worker still owns the
job at commit time.

The result fence delegates the final decision to an atomic job-store
ownership/completion operation. A stale worker therefore cannot overwrite a
new owner's result, and duplicate completion is rejected.

This closes the dangerous race:

1. worker A owns a job;
2. A loses its lease;
3. recovery gives the job to worker B;
4. B completes the job;
5. A finally returns with an old result.

A's result is rejected at the commit boundary.
