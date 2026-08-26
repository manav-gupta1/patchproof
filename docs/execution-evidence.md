# Execution-derived authoritative evidence

Scanner, test, and verification results now have explicit execution-artifact
representations.

The authoritative bundle is generated from those results rather than from
manually supplied summary strings.

Each execution artifact is hashed independently. The execution evidence then
has its own canonical SHA-256 digest.

A failed verification cannot produce an authoritative bundle.

The durable `EvidenceBundle` remains the compact publication record, while the
execution evidence captures the provenance of the scanner/test/verification
outputs used to construct it.
