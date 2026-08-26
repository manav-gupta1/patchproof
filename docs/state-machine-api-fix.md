# Job state machine API reconciliation

The durable verification service already depended on a job-oriented state
machine API (`create`, `state`, `mark_*`, and job-id based `fail`), while the
state machine implementation had only record-level transitions.

The state machine now owns an in-memory job registry for that service contract
while retaining the record-level transition API and transition validation.
