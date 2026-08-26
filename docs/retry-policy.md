# Retry and recovery policy

Failures are classified into retryable and permanent classes.

Retryable failures use bounded exponential backoff with jitter:

`base * 2^(attempt-1)`, capped by `max_delay`.

Retries stop when `max_attempts` is reached. Permanent failures never retry.

Retry schedules and the last error are persisted in SQL so a process restart
does not reset the retry budget.

Publication remains idempotent through the durable publication transaction;
retries therefore do not imply a second branch push or duplicate PR.
