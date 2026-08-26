# GitHub webhook → job flow

```text
GitHub
  ↓
POST /webhooks/github
  ↓
HMAC SHA-256 verification
  ↓
JSON parsing
  ↓
supported event check
  ↓
delivery-ID idempotency
  ↓
durable remediation job
  ↓
Celery enqueue
```

The webhook endpoint must acknowledge only after signature validation and durable
job creation. Duplicate deliveries do not create duplicate remediation jobs.

Supported events are `code_scanning_alert` and `check_run`.

Only the repository and exact commit SHA are extracted from the event into the
remediation job. The worker remains responsible for the actual remediation
pipeline.
