# FastAPI + Celery bridge

The runtime path is now:

```text
GitHub
  ↓ HTTPS
POST /webhooks/github
  ↓
HMAC validation
  ↓
delivery idempotency
  ↓
durable job
  ↓
Celery remediation_task.delay(job_id)
  ↓
RemediationOrchestrator.run(job_id)
```

`/healthz` is intentionally independent of GitHub and worker state so it can
be used for basic HTTP liveness checks.

Celery keeps late acknowledgements, prefetch=1, worker-loss rejection, and
bounded task execution times. The orchestrator is configured at application
bootstrap rather than imported as a global singleton, keeping tests and staging
wiring deterministic.
