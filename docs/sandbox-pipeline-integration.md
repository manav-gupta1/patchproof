# Verification pipeline -> sandbox integration

The verification pipeline no longer executes repository commands through its
own host-side command runner.

Both scanner and test commands now go through `SandboxExecutionService`, which
owns the gVisor/runsc boundary.

This establishes the intended production architecture:

```text
verification pipeline
        ↓
SandboxExecutionService
        ↓
temporary workspace
        ↓
gVisor/runsc
        ↓
repository command
```

The pipeline can inject a sandbox implementation for deterministic tests, while
production uses the real gVisor adapter.
