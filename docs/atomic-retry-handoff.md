# Atomic retry handoff

The retry token and worker lease are now transferred in one database
transaction.

The dispatcher first finds candidate retry IDs, but `RetryHandoff.claim()` is
the correctness boundary. It rechecks that the retry is due, atomically
acquires the job lease, and deletes the retry record in the same transaction.

Therefore a crash before commit leaves both the retry and job untouched; a
successful commit leaves the worker lease and consumed retry together.

The actual worker pipeline begins only after this durable handoff succeeds.
