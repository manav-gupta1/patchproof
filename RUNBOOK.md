# PatchProof Operator Runbook

Operations guide for running, monitoring, and troubleshooting PatchProof.

---

## 1. Quick Start (Docker Compose)

For complete staging deployment instructions, see [STAGING_DEPLOYMENT.md](file:///Users/manav/PatchProof/patchproof/STAGING_DEPLOYMENT.md).

```bash
# 1. Build container images
docker compose build

# 2. Start full stack with persistent volumes in background
docker compose up -d

# 3. Check service health
docker compose ps

# 4. Run staging smoke test (dual-mode)
python -m pytest -v tests/test_staging_smoke_integration.py
```

---

## 2. Health & Readiness Verification

```bash
# Liveness probe (HTTP 200 {"status": "ok"})
curl -f http://localhost:8000/healthz

# Readiness probe (HTTP 200 {"status": "ready"})
curl -f http://localhost:8000/readyz

# Web UI accessibility
curl -i http://localhost:3000/
```

---

## 3. Logs & Observability

```bash
# View API service logs
docker compose logs --tail=100 -f api

# View Celery remediation worker logs
docker compose logs --tail=100 -f worker

# View Web GUI logs
docker compose logs --tail=100 -f gui
```

---

## 4. Troubleshooting Guide

### Webhook Returns 401 Unauthorized
- **Cause**: Inbound `X-Hub-Signature-256` header does not match computed HMAC-SHA256 signature.
- **Check**: Verify `GITHUB_WEBHOOK_SECRET` matches the secret configured in GitHub Webhooks settings.

### Job Remains in `QUEUED` State
- **Cause**: Celery worker is offline or Redis queue connection is blocked.
- **Check**:
  ```bash
  docker compose ps worker redis
  docker compose logs --tail=50 worker
  ```

### Verification Failed (`state: failed`)
- **Cause**: The candidate patch did not pass AST validation, test execution, or security rescan in the sandbox.
- **Expected Invariant**: Zero GitHub writes occur on failed verification.
- **Action**: Inspect `error` and `verification_results` in `GET /jobs/{job_id}` or Job Detail UI.

### SSE Disconnects or Falls Back to Polling
- **Cause**: Proxy buffer timeout or client network disconnect.
- **Expected Invariant**: Frontend seamlessly switches to automated polling fallback (`● Polling Fallback`).

### GitHub Publication Fails (403 or Rate Limit)
- **Cause**: GitHub App installation lacks `write` permissions or exceeded secondary rate limits.
- **Check**: Verify GitHub App repository permissions in GitHub Organization Settings.
