# Three-boundary reconciliation

- Re-exported the canonical `JobState` from the persistence package boundary.
- Re-exported the existing `VerificationEngine` alongside the current runner.
- Migrated the production Semgrep verifier from removed `SandboxRequest` /
  `execute()` to the current `SandboxExecutor.run(argv)` contract.

No legacy sandbox request type was recreated.
