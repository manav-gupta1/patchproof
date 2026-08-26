# PatchProof Staging Deployment Guide

This document outlines the architecture, environment variables, startup procedures, operational checks, and troubleshooting runbooks for deploying **PatchProof** to a staging environment.

---

## 1. Staging Architecture Overview

PatchProof operates as a multi-container service orchestrated via Docker Compose or Kubernetes:

```text
                                Internet
                                   │
                     ┌─────────────┴─────────────┐
                     ▼                           ▼
            ┌─────────────────┐         ┌─────────────────┐
            │   Web GUI       │         │   FastAPI API   │
            │   Port 3000     │         │   Port 8000     │
            │   (Next.js)     │         │   (Uvicorn)     │
            └────────┬────────┘         └────────┬────────┘
                     │                           │
                     │                           ▼
                     │                  ┌─────────────────┐
                     │                  │  Redis Broker   │
                     │                  │  Port 6379      │
                     │                  └────────┬────────┘
                     ▼                           ▼
            ┌─────────────────┐         ┌─────────────────┐
            │   PostgreSQL    │◄────────│  Celery Worker  │
            │   Port 5432     │         │  (Remediation)  │
            └─────────────────┘         └─────────────────┘
```

### Services
1. **`postgres`**: PostgreSQL 16 database storing jobs, events, evidence bundles, and policies. Backed by persistent volume `postgres_data`.
2. **`redis`**: Redis 7 message broker and result backend for asynchronous Celery remediation workers. Backed by persistent volume `redis_data`.
3. **`api`**: FastAPI service handling webhook ingestion, job state transitions, Server-Sent Events (SSE), evidence export, and tenant auth.
4. **`worker`**: Celery worker executing isolated workspace staging, Semgrep vulnerability scanning, AST patch generation, isolated verification, and GitHub App publication.
5. **`gui`**: Next.js 14 web application providing the central security operations control panel, live SSE streams, KPI cards, and evidence verification.

---

## 2. Staging Environment Configuration

Create a `.env.staging` file on the staging host:

```ini
# Environment
PATCHPROOF_ENVIRONMENT=staging
PATCHPROOF_AUTH_ENABLED=true
PATCHPROOF_API_KEY=your_secure_staging_api_key_here
GITHUB_WEBHOOK_SECRET=your_secure_github_webhook_secret_here

# Database & Broker
POSTGRES_DB=patchproof
POSTGRES_USER=patchproof
POSTGRES_PASSWORD=your_secure_postgres_password_here
PATCHPROOF_DATABASE_URL=postgresql+psycopg://patchproof:your_secure_postgres_password_here@postgres:5432/patchproof
PATCHPROOF_REDIS_URL=redis://redis:6379/0

# CORS & Networking
PATCHPROOF_CORS_ORIGINS=https://staging.patchproof.io,https://staging-api.patchproof.io
NEXT_PUBLIC_API_URL=https://staging-api.patchproof.io
INTERNAL_API_URL=http://api:8000

# GitHub App Credentials (for staging publication)
GITHUB_APP_ID=123456
GITHUB_APP_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----"
GITHUB_INSTALLATION_ID=789012
```

---

## 3. Staging Deployment Commands

### 1. Build and Start Services
```bash
# Export staging environment
export $(cat .env.staging | xargs)

# Build and start all containers in background
docker compose -f docker-compose.yml up -d --build
```

### 2. Verify Container Status
```bash
docker compose ps
```

All 5 containers (`postgres`, `redis`, `api`, `worker`, `gui`) must report `healthy` or `running`.

### 3. Verify Health and Readiness
```bash
# Liveness probe (HTTP 200 {"status": "ok"})
curl -f http://localhost:8000/healthz

# Readiness probe (HTTP 200 {"status": "ready"})
curl -f http://localhost:8000/readyz

# Web GUI HTTP 200
curl -I http://localhost:3000/
```

---

## 4. GitHub App & Webhook Configuration

1. **GitHub App Settings**:
   - **Webhook URL**: `https://staging-api.patchproof.io/webhooks/github`
   - **Webhook Secret**: Set to `GITHUB_WEBHOOK_SECRET`.
   - **Permissions**:
     - *Repository permissions*:
       - `Pull requests`: Read & Write
       - `Contents`: Read & Write
       - `Checks`: Read & Write
       - `Code scanning alerts`: Read
     - *Subscribe to events*:
       - `Pull request`
       - `Check run`
       - `Code scanning alert`
       - `Push`
       - `Installation`
       - `Installation repositories`
2. **Install App**:
   - Install the GitHub App on your dedicated staging test organization/repository.

---

## 5. Controlled Staging Smoke Test

To run the controlled smoke test against the dedicated staging repository:

```bash
PATCHPROOF_GITHUB_INTEGRATION_TEST=true \
PATCHPROOF_TEST_REPOSITORY=patchproof-staging/dedicated-test-repo \
GITHUB_APP_ID=123456 \
GITHUB_APP_PRIVATE_KEY_PATH=/path/to/private-key.pem \
python -m pytest -v tests/test_staging_smoke_integration.py
```

---

## 6. Operational Runbook & Logs

### View Logs
```bash
# View API service logs
docker compose logs --tail=100 -f api

# View Celery remediation worker logs
docker compose logs --tail=100 -f worker

# View Next.js Web GUI logs
docker compose logs --tail=100 -f gui
```

### Stop / Shutdown Services
```bash
docker compose down
```

### Rollback / Data Cleanup
```bash
# Stop containers and remove volumes (clean wipe)
docker compose down -v
```
