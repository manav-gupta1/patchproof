# Production infrastructure

PatchProof now has explicit infrastructure adapters:

- PostgreSQL via SQLAlchemy for durable job state.
- Redis as Celery broker/result backend.
- Celery worker configuration with late acknowledgements.
- Worker prefetch of 1 to reduce concurrent untrusted repository execution.
- Hard/soft task time limits.
- Automatic retries with exponential backoff for transient `RuntimeError`s.

The remediation runtime remains a separate dependency-injection boundary.
It must create the repository workspace, invoke SandboxRunner, VerificationEngine,
and persist state transitions. It must never execute customer code in the API
process.

Development services can be started from `docker-compose.infra.yml`.
The included database password is development-only and must not be used in
production.
