# Real GitHub adapter

The publication layer now has a real GitHub REST boundary.

It requires runtime credentials, uses GitHub's JSON API, records the evidence
SHA-256 in the PR body, and searches for an existing matching PR before create.

The adapter contains no verification logic; `VerifiedPublicationService`
remains the gate in front of it.

Credentials are runtime configuration and are not stored in the repository.
