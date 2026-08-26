# Real execution verification pipeline

The verification layer now has a concrete execution boundary.

`RealVerificationPipeline` runs:

1. Semgrep against the repository;
2. the repository's pytest suite;
3. a deterministic verification decision based on those exit/results.

Raw stdout/stderr is retained in the execution artifacts and is hashed as part
of the evidence.

The implementation is intentionally fail-closed: a non-zero scanner or test
execution means verification does not pass.

This is the application-level runner boundary. Production should execute it
inside the already-planned isolated sandbox/gVisor worker rather than directly
inside the API process.
