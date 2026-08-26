# Verification and gVisor

The verification boundary now requires every configured check to pass.

Default architecture:

```text
patched workspace
      ↓
gVisor sandbox (runsc)
      ↓
repository tests
      ↓
Semgrep rescan
      ↓
patch-applied check
      ↓
VerificationResult
      ↓
evidence_id (SHA-256)
```

A failed test or failed Semgrep rescan means `verified=false`.

The gVisor adapter expects the host/container runtime to already be configured
with `runsc`. PatchProof application code must never install or configure a
privileged runtime from inside a customer job.

Evidence is serialized with a schema version and timestamp. The evidence ID is
a deterministic SHA-256 digest over the verification inputs and results.
