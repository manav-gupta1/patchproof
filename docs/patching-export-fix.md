# Patching package export fix

The repository already contains a concrete `PatchAgent` implementation and
patch contracts. The E2E fixture failed because those existing symbols were
not exported by `packages.patching`.

The package boundary now exports the existing PatchAgent, PatchCandidate,
PatchOperation, PatchRequest, PatchApplier, PatchEngine, and related types.
No duplicate implementation was introduced.
