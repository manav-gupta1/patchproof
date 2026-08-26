# Recovery reconciler

The recovery layer now reconciles expired `dispatched` retry records against
the authoritative SQL job state.

- A dispatched retry whose job succeeded is finalized and removed.
- A dispatched retry whose job did not complete is returned to `queued`.
- Missing jobs are retained rather than destructively deleted.

This makes recovery state-driven rather than timer-only and prevents a retry
from being permanently lost after a dispatcher or worker crash.
