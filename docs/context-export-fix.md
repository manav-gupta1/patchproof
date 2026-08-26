# Context export fix

The E2E fixture imports `SourceSpan` from `packages.context`. The existing
`SourceSpan` implementation was located in the context models module but was
not exported at the package boundary. The package export was corrected and
the current verification/durable/E2E integration gate was rerun.
