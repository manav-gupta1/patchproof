# Retry execution

The retry dispatcher now executes due retry records through the actual worker
pipeline.

A retry is dispatched only after the SQL job lease is acquired. The retry
record is then consumed and the normal worker owns execution, heartbeat,
verification, publication, and terminal job state.

A second worker cannot execute the same retry because it cannot acquire the
live job lease.

The dispatcher records execution outcomes; retry classification/backoff remains
the responsibility of the retry policy layer.
