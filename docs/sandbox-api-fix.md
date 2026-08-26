# Sandbox API export fix

The E2E exploit verifier imports `CommandResult` from `packages.sandbox`.
The concrete `CommandResult` implementation already lives in
`packages.execution.runner`; it is now re-exported from the sandbox package
boundary.

No duplicate result type was introduced.
