# Staging runbook

Staging is isolated from production.

1. Install the GitHub App only on a dedicated staging repository.
2. Grant only the repository permissions required by the remediation flow.
3. Configure and verify the GitHub webhook signature.
4. Supply private keys, database credentials, and model API keys via a secret manager.
5. Configure gVisor `runsc` on the worker host; the application never installs it.
6. Start PostgreSQL, Redis, API, and worker.
7. Send a controlled code-scanning event.
8. Confirm the durable job progresses through the state machine.
9. Confirm tests and Semgrep rescan run inside the sandbox.
10. Confirm only `verified=true` can create a staging PR.
11. Inspect `job_events` for the complete audit trail.

Rollback: disable the staging GitHub App/webhook and stop workers. Production is
not affected because the staging installation and database are separate.
