# Test API migration

Exported the existing `DeterministicPatchModel` implementation from the
patching package boundary.

Migrated Semgrep/exploit test doubles from the removed `SandboxRequest` /
`execute()` interface to the current `ExecutionRequest` / `run(argv)`
contract. No legacy sandbox type was recreated.
