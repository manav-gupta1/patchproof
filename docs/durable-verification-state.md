# Durable verification + state gate

The sandbox execution pipeline is now connected to durable evidence and the job
state machine.

A job can reach `VERIFIED` only when:

1. the job is already in `VERIFYING`;
2. sandbox execution completes;
3. scanner and tests pass;
4. authoritative evidence is constructed from those execution results;
5. the evidence is persisted successfully;
6. only then is the durable state transitioned to `VERIFIED`.

If verification fails, the job transitions to `FAILED` and no evidence bundle is
persisted as authoritative.

This establishes the publication precondition:

```text
sandbox execution
      ↓
authoritative evidence
      ↓
durable evidence persistence
      ↓
VERIFIED
      ↓
GitHub publication
```
