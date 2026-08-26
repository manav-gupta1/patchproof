# Durable worker orchestration

Jobs now have explicit worker ownership and leases.

Lifecycle:

`QUEUED -> RUNNING -> SUCCEEDED | FAILED`

A worker must claim a job before executing it. A live lease prevents another
worker from claiming the same job.

If a worker dies and its lease expires, another worker can reclaim the job.
The old worker cannot complete the job after ownership has moved.

Successful jobs are terminal and are not executed again.

The in-memory implementation defines the concurrency and recovery contract;
the same atomic claim/lease semantics should be implemented by the production
SQL store.
