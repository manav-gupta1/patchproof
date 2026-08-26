# Changelog

All notable changes to **PatchProof** are documented in this file.

---

## [0.1.0] - 2026-08-25 - PatchProof MVP Release Candidate

### Added
- **Evidence-First Remediation Pipeline**: End-to-end automated pipeline for scanning vulnerabilities, generating AST-based patches, executing isolated sandbox verification, signing cryptographic evidence with Ed25519, and publishing verified pull requests.
- **Verification Gate Safety Invariant**: Strict invariant guaranteeing zero GitHub remote writes (no branch creation, no commits, no PRs) if verification fails or is incomplete.
- **Production GitHub App Integration**: Asymmetric RS256 App JWT signing, thread-safe installation access token caching, repository authorization, protected branch guards, and idempotent PR deduplication.
- **Controlled Real-GitHub Integration Harness**: Opt-in testing harness (`PATCHPROOF_GITHUB_INTEGRATION_TEST=true`) with dedicated test repository safety guards.
- **Real-Time SSE Event Streaming**: Server-Sent Events endpoints for job-level (`GET /jobs/{job_id}/events`) and tenant-wide (`GET /events`) lifecycle event streaming with `Last-Event-ID` reconnection and automated polling fallback.
- **PatchProof Central Operations Dashboard**: Next.js 14 web application featuring real-time KPI metrics, job status filters, live SSE connection badges, non-blocking toast notifications, and interactive Job Detail pages with cryptographic evidence verification.
- **Multi-Tenant Security & Horizontal Privilege Escalation Protection**: Strict tenant isolation and repository authorization on all API routes.
- **Production Configuration Guard**: Fail-closed configuration validator preventing startup in production with default secrets or disabled authentication.
