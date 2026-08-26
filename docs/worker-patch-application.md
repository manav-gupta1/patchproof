# Worker patch application

The deterministic/reference patch provider can supply complete-file
replacements through `PatchCandidate.files`. The patch applier previously
ignored that field after the structured `operations` migration, causing the
worker to report success without changing the workspace.

The applier now converts complete-file replacements into the same bounded,
exact replacement path. Structured `operations` remains the preferred
production contract.
