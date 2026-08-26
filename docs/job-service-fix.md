# Job service/state contract fix

`JobService` was already written against a richer `JobRecord` contract than
the record implementation provided. The record now carries delivery ID,
attempt/error metadata, and timestamps, and `JobStateMachine` supports the
record-oriented transition/failure operations used by the service while
retaining the existing enum-oriented API.

The obsolete CLONING test remains a separate historical API mismatch and was
not reintroduced into the current state machine.
