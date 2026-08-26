# Semgrep security gate

The E2E security acceptance test now resolves `semgrep` through PATH before
execution. A missing executable fails the gate explicitly instead of surfacing
as a raw subprocess `PermissionError`.

The security gate is intentionally fail-closed: no substitute analyzer is
treated as equivalent to Semgrep.
