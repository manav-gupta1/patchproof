# PatchProof Release Checklist (MVP v0.1.0)

Every item below has been executed and verified in the automated test suites and local runtime environments.

---

## Pre-Release Verification Checklist

- [x] **Backend Tests**: 513 passed, 4 skipped, 1 warning (100% green).
- [x] **Frontend Tests**: 27 passed across 9 Vitest suites (100% green).
- [x] **Next.js Production Build**: Compiled cleanly with 0 type errors across all 8 routes.
- [x] **Docker Multi-Stage Build**: API, Celery worker, Web GUI, Redis, PostgreSQL containers with persistent volumes.
- [x] **Liveness Probe (`/healthz`)**: HTTP 200 `{"status": "ok"}`.
- [x] **Readiness Probe (`/readyz`)**: HTTP 200 `{"status": "ready"}`.
- [x] **Webhook Signature Verification**: Constant-time `hmac.compare_digest` with 5MB max payload limit.
- [x] **GitHub App Installation Lifecycle**: Handles `installation` (created/deleted/suspended) & `installation_repositories` (added/removed).
- [x] **Repository Access Synchronization**: Inbound webhooks strictly validated against active installation repository grants.
- [x] **Cryptographic Evidence JSON Export**: `GET /jobs/{job_id}/evidence/export` downloadable audit bundle with signature preservation.
- [x] **Repository Policy Management**: `GET/PUT /repositories/{owner}/{repo}/policy` with tenant isolation and validation.
- [x] **Multi-Tenant Isolation**: Horizontal privilege escalation blocked with HTTP 403 Forbidden.
- [x] **Workspace Isolation**: Clean isolated temporary staging (`patchproof-ws-*`) with automatic cleanup.
- [x] **Path Traversal Protection**: Unified diff and file patch applier enforce `path.relative_to(root)`.
- [x] **Verification Gate**: Mandatory safety gate `UNVERIFIED PATCH -> ZERO GITHUB WRITES`.
- [x] **Cryptographic Evidence Integrity**: Canonical SHA-256 digest + Ed25519 digital signature binding.
- [x] **Zero-Write Negative Failure Path**: Verification failure aborts without creating branches, commits, or PRs.
- [x] **Real-Time SSE Streaming**: Job-level (`GET /jobs/{job_id}/events`) and tenant-wide (`GET /events`) with `Last-Event-ID` reconnection.
- [x] **Automated Polling Fallback**: Web GUI automatically degrades to polling if SSE is disconnected.
- [x] **GitHub App JWT Authentication**: RS256 signing with 10-minute expiry and clock-skew mitigation.
- [x] **Installation Token Caching**: Thread-safe in-memory cache with auto-refresh within 60s of expiration.
- [x] **Idempotent Pull Request Creation**: Embedded comment markers prevent duplicate PRs during worker retries.
- [x] **Controlled Staging Smoke Harness**: Dual-mode (`SAFE DEFAULT` skips; `LIVE MODE` executes controlled lifecycle with cleanup).
- [x] **Production Configuration Guard**: Rejects insecure default secrets and disabled authentication in production mode.
- [x] **Zero Secret Leakage Audit**: Private keys, tokens, JWTs, and webhook secrets scrubbed from logs and outputs.
