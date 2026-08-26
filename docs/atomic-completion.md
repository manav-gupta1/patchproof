# Atomic completion protocol

Final job completion is now one database operation.

The conditional `UPDATE` requires all completion preconditions simultaneously:

- the job is still `running`;
- the committing worker is still the recorded owner;
- the lease is still live.

Only then does the same operation transition the job to `succeeded`, persist
the result, and clear ownership.

This closes the final timing gap between checking a lease and publishing a
result: a stale worker cannot pass an earlier check and then overwrite the
authoritative state.
