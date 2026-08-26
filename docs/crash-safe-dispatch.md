# Crash-safe retry dispatch

A retry is transitioned from `queued` to `dispatched` in the same transaction
that acquires the SQL job lease. The retry token remains durable until the
worker reaches completion.

If a dispatcher or worker dies after handoff, the `dispatched` record remains.
After its dispatch lease expires, recovery moves it back to `queued`, closing
the crash window between lease acquisition and actual execution.
