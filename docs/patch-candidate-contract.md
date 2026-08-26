# Patch candidate contract reconciliation

The current `PatchApplier` already consumes `PatchCandidate.operations`, but
the model did not define that field and instead exposed only a legacy `files`
mapping. The model now contains the concrete `PatchOperation` contract used
by the applier and current E2E flow.

The E2E fixture no longer imports the obsolete `PatchAgent`/`PatchRequest`
API.
