# PatchProof

**Evidence-first security remediation prototype**

PatchProof explores a guarded workflow for turning repository security findings into proposed code changes:

`Finding → Analysis → Exploit reproduction → Patch → Verification → Evidence → Pull request`

The project is an active prototype. The repository contains webhook signature validation, finding normalization, remediation job models, pipeline orchestration interfaces, evidence handling, and GitHub publication components. The API entry point currently uses in-memory job and queue implementations; it is not yet a durable, production deployment.

## What is implemented

- GitHub webhook HMAC-SHA256 signature verification.
- Normalization for code-scanning, check-run, and pull-request events.
- Remediation job and state-machine models.
- A pipeline boundary that sequences analysis, exploit reproduction, patch generation, verification, evidence creation, and PR publication.
- A GitHub publisher that checks verification evidence before publication.

## Important current limitations

- The API currently stores jobs and queued tasks in process memory. Restarting the API loses them.
- The API currently creates a development webhook secret fallback. Configure a strong `GITHUB_WEBHOOK_SECRET` and remove development defaults before exposing the service.
- The API entry point currently accepts a webhook and enqueues a task; a durable worker integration is still required to execute the remediation pipeline.
- Production model integration, sandbox isolation, durable persistence, delivery deduplication, and deployment hardening remain work in progress.
- Do not treat the README pipeline diagram as proof that every stage is fully wired into a deployed end-to-end service.

## Architecture

```text
GitHub Security Event
        |
        v
Webhook Signature Validation
        |
        v
Finding Normalization
        |
        v
Remediation Job + Queue
        |
        v
Checkout → Analyze → Reproduce → Patch
                                |
                                v
                    Tests / Static Analysis
                                |
                                v
                         Evidence Record
                                |
                                v
                     Human-reviewable PR
```

The orchestration layer is deliberately separated from concrete model, exploit, patch, verification, evidence-store, and GitHub client implementations.

## Repository layout

- `apps/api/`: FastAPI application and webhook entry point.
- `packages/github/`: GitHub webhook and publication integration.
- `packages/orchestration/`: remediation job models, state machine, and pipeline.
- `packages/evidence/`: evidence construction and storage abstractions.
- `packages/`: shared application components.

## Local setup

Python 3.12 or newer is required.

```bash
git clone https://github.com/manav-gupta1/patchproof.git
cd patchproof
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Set the required application settings and webhook secret in your environment. The settings model requires `DATABASE_URL` and `REDIS_URL`; the webhook handler reads `GITHUB_WEBHOOK_SECRET`.

```bash
export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/patchproof"
export REDIS_URL="redis://localhost:6379/0"
export GITHUB_WEBHOOK_SECRET="replace-with-a-long-random-secret"
uvicorn apps.api.main:app --reload
```

The API health endpoint is `/health`. Use a GitHub webhook configured with the `/webhooks/github` endpoint and the same secret.

> The current API queue is an in-memory test implementation. The environment settings and package dependencies do not by themselves mean that PostgreSQL or Redis persistence is wired into this entry point.

## Safety model

Automated code changes should not be published solely because an LLM generated them. The intended design requires exploit reproduction, verification gates, evidence tied to the source commit and patch digest, and human review through a pull request. Repository checkout, patch execution, and tests must run in an isolated, resource-limited environment before production use.

## Roadmap

- [ ] Replace in-memory API job storage with durable persistence.
- [ ] Replace the in-memory queue with a durable worker system.
- [ ] Enforce webhook delivery idempotency and replay handling.
- [ ] Require explicit production secrets and configuration validation.
- [ ] Complete isolated repository checkout and patch execution.
- [ ] Add integration tests for the complete webhook-to-PR path.
- [ ] Add production model-provider integration and deployment hardening.

## License

No license has been added yet. All rights reserved unless and until a license is specified.
