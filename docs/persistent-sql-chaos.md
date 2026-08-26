# Persistent SQL process chaos

The process-level crash tests now use a persistent SQLite database.

A worker process claims a real database row and is then terminated before
completion. The next process observes the durable `running` state, recovery
requeues the abandoned job, and a new worker completes it.

The suite also verifies that the old worker cannot later overwrite the
authoritative result.

This connects process termination directly to persistent job state rather
than an in-memory or file-event simulation.
