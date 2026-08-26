# E2E current sandbox migration

Migrated the vulnerable-Python acceptance fixture from the obsolete
`SandboxRequest`/`execute()`/`CommandResult` API to the current
`SandboxExecutor.run(argv) -> SandboxResult` contract.

The fixture now:
1. runs the baseline proof with the current sandbox contract,
2. applies the existing patch,
3. runs the proof, test suite, and semgrep gates through the same current
   contract.

No legacy sandbox types were reintroduced.
