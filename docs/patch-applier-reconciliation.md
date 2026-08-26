# Patch applier reconciliation

`PatchCandidate` is the current structured patch contract and exposes
`operations`. The applier was still consuming the obsolete dictionary
contract (`proposal.get("patch")`).

The applier now performs exact, repository-bounded text replacements from
`PatchCandidate.operations`, matching the current model and preserving the
path/unique-match safety checks.
