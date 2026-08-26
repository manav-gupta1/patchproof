# Interface reconciliation

Reconciled concrete API names where a current implementation already existed:

- `LocalSandboxRunner` aliases the current `GVisorCommandRunner`.
- `FailureCode` is exported from the orchestration models.
- GitHub's current `PublicationRejected` remains authoritative; the older
  `PublicationDenied` name is a compatibility alias.
- `VerificationEvidence` is implemented as a small immutable evidence contract
  with commit binding validation.

These changes are compatibility work, not placeholder business logic.
