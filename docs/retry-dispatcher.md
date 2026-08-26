# Durable retry dispatcher

Due retry records are now dispatched through the same SQL job lease used by
normal workers.

Dispatch sequence:

1. Find retry records whose `next_run_at` is due.
2. Attempt to acquire the authoritative job lease.
3. Only after the lease is acquired, remove the retry schedule.
4. Execute the job under the existing worker/heartbeat/retry machinery.
5. A subsequent failure may create a new durable retry schedule.

This prevents two workers from executing the same retry simultaneously and
keeps retry scheduling durable across process restarts.

A retry record for a missing job is retained rather than destructively deleted.
