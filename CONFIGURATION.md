# PatchProof Configuration Reference

This guide documents the environment configuration for PatchProof across **development**, **test**, **controlled integration**, and **production** environments.

---

## 1. Core Environment Variables

| Variable | Required in Prod | Default (Dev) | Description |
| :--- | :--- | :--- | :--- |
| `PATCHPROOF_ENVIRONMENT` | Yes | `development` | Operating mode: `development`, `test`, `production`. |
| `PATCHPROOF_AUTH_ENABLED` | Yes | `true` | Enforces multi-tenant API key authentication. Must be `true` in production. |
| `PATCHPROOF_API_KEY` | Yes | `patchproof_dev_api_key` | Master / tenant API key for authenticating REST requests. |
| `GITHUB_WEBHOOK_SECRET` | Yes | `development-secret` | HMAC-SHA256 secret for validating inbound GitHub webhook signatures. (Must be >= 16 chars in production). |
| `PATCHPROOF_SIGNING_KEY` | Optional | Generated on start | Ed25519 private key PEM for cryptographic evidence signing. |

---

## 2. GitHub App Integration Configuration

| Variable | Required in Prod | Default | Description |
| :--- | :--- | :--- | :--- |
| `GITHUB_APP_ID` | Yes (for PRs) | None | GitHub App ID registered on GitHub. |
| `GITHUB_APP_PRIVATE_KEY` | Yes (for PRs) | None | RSA private key PEM (RS256) for generating App JWTs. |
| `GITHUB_APP_PRIVATE_KEY_PATH` | Alternative | None | Absolute path to RSA private key file on filesystem. |
| `GITHUB_INSTALLATION_ID` | Optional | Auto-resolved | Fallback GitHub App installation ID. |
| `GITHUB_API_URL` | Optional | `https://api.github.com` | Base URL for GitHub REST API (set for GitHub Enterprise Server). |

---

## 3. Database & Redis Queue

| Variable | Required in Prod | Default (Dev) | Description |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | Yes | `sqlite:///patchproof.db` | PostgreSQL connection string (`postgresql+psycopg2://user:pass@host:5432/patchproof`). |
| `REDIS_URL` | Yes | `redis://localhost:6379/0` | Redis broker and results backend for Celery workers. |
| `CELERY_BROKER_URL` | Optional | Mirrors `REDIS_URL` | Celery broker URL. |

---

## 4. Remediation Sandbox Execution

| Variable | Mode | Supported Options | Description |
| :--- | :--- | :--- | :--- |
| `PATCHPROOF_SANDBOX_PROVIDER` | Optional | `gvisor`, `docker`, `bubblewrap` | Execution isolation runtime. Multi-tenant production requires `gvisor` (`runsc`). |
| `PATCHPROOF_SANDBOX_TIMEOUT_SEC` | Optional | `30` | Maximum timeout in seconds for verification subprocess execution. |
| `PATCHPROOF_SANDBOX_MEMORY_MB` | Optional | `512` | Memory boundary limit per remediation test runner. |

---

## 5. Controlled Real-GitHub Integration (Opt-In Only)

| Variable | Required for Test | Description |
| :--- | :--- | :--- |
| `PATCHPROOF_GITHUB_INTEGRATION_TEST` | `true` | Explicit opt-in flag. Refuses to write to remote GitHub unless enabled. |
| `PATCHPROOF_TEST_REPOSITORY` | `owner/repo` | Strictly isolated test repository. Runner refuses to operate on any other repository. |

---

## 6. Secret Security Rules

1. **Zero Secret Logging**: Private keys, JWTs, installation access tokens, and webhook secrets are never serialized to logs, API responses, or SSE events.
2. **Safe Diagnostics**: Diagnostic commands report only `configured: yes` or `configured: no`.
3. **Fail-Closed Guard**: The production configuration guard ([`packages/config/guard.py`](file:///Users/manav/PatchProof/patchproof/packages/config/guard.py)) prevents startup if production mode is set with insecure secrets or disabled authentication.
