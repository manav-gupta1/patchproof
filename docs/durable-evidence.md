# Durable verification evidence

Verification output is now represented by an immutable `EvidenceBundle`.

It records:

- job ID
- target commit SHA
- exact patch SHA-256
- scanner summary
- test summary
- verification summary
- canonical evidence SHA-256

The evidence hash is computed over canonical JSON with sorted keys and stable
separators, so the same evidence content produces the same digest.

`EvidenceStore` persists one evidence bundle per job. Re-submitting identical
evidence is idempotent; submitting different evidence for an existing job is
rejected.

Migration `0002_evidence_bundles` adds the production table. The existing
Alembic bootstrap will apply it automatically with `upgrade head`.
