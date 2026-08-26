# Verified -> GitHub PR end-to-end boundary

The publication path is now explicitly bound together:

```text
verification evidence
        ↓
durable job state == verified
        ↓
stable publication marker
        ↓
GitHub App installation token
        ↓
idempotent PR lookup/create
        ↓
PR reference
```

The marker contains the job ID, target commit SHA, and patch SHA-256. This makes
the publication operation retry-safe.

The integration tests cover both:
- repeated publication calls;
- a network timeout after GitHub has already created the PR.

In both cases exactly one PR creation request is issued.
