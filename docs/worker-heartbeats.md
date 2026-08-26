# Worker lease heartbeats

Long-running verification and publication are protected by a background lease
heartbeat.

The worker acquires a lease, renews it before expiry, and fences itself if a
heartbeat fails. A worker that loses ownership must not mark the job successful
or overwrite a replacement worker's state.

The heartbeat interval must be strictly shorter than the lease duration.
