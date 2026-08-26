# Staging integration test

The repository now includes an integration-level HTTP test covering the first
real production boundary:

```text
GitHub-shaped request
  -> FastAPI
  -> signature validation
  -> webhook parsing
  -> delivery idempotency
  -> durable-job adapter
  -> queue adapter
```

The test deliberately does not fake cryptographic verification or bypass the
HTTP endpoint.

For actual staging, run `scripts/staging-smoke.sh`, start the staging compose
stack, and use only a dedicated staging GitHub repository. The external LLM,
GitHub App, PostgreSQL, Redis, and gVisor services must be supplied by staging
infrastructure; this environment does not contain those production secrets.
