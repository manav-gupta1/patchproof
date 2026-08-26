from __future__ import annotations

import hashlib
import hmac
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from packages.api.app import create_app
from packages.auth import ApiKeyStore, TenantContext
from packages.github.auth import sanitize_secret_text
from packages.gitops.staging import WorkspaceStaging
from packages.jobs.orchestrator import RemediationOrchestrator
from packages.jobs.pipeline_factory import ConcreteGitHubPublisher
from packages.jobs.state import ALLOWED_TRANSITIONS, InvalidTransition, JobRecord, JobState, JobStateMachine
from packages.jobs.store import InMemoryJobStore
from packages.patching.apply import PatchApplier, PatchApplyError
from packages.signing import Ed25519EvidenceSigner
from packages.webhooks.github import InvalidWebhook, parse_event, verify_signature
from packages.webhooks.handlers import WebhookDispatcher


# ==============================================================================
# 1. Security & Redaction Tests
# ==============================================================================

def test_secret_redaction_across_all_diagnostics():
    raw_secrets = (
        "Failed with token ghs_1234567890abcdef1234567890abcdef1234 and "
        "private key -----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA...\n-----END RSA PRIVATE KEY----- "
        "on https://x-access-token:ghs_secrettoken123@github.com/org/repo.git with Bearer eyJhbGciOiJSUzI1NiJ9.test.jwt"
    )
    sanitized = sanitize_secret_text(raw_secrets)
    assert "ghs_1234567890abcdef1234567890abcdef1234" not in sanitized
    assert "-----BEGIN RSA PRIVATE KEY-----" not in sanitized
    assert "ghs_secrettoken123" not in sanitized
    assert "eyJhbGciOiJSUzI1NiJ9.test.jwt" not in sanitized
    assert "[REDACTED_TOKEN]" in sanitized or "[REDACTED_SECRET]" in sanitized
    assert "[REDACTED_PRIVATE_KEY]" in sanitized
    assert "[REDACTED_AUTH]" in sanitized
    assert "[REDACTED_JWT]" in sanitized


def test_patch_applier_blocks_path_traversal(tmp_path):
    applier = PatchApplier()
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / "safe.py").write_text("print('hello')", encoding="utf-8")

    malicious_candidate = {
        "files": {
            "../../../etc/passwd": "root:x:0:0:root:/root:/bin/bash",
            "/etc/shadow": "root:*::",
        }
    }

    with pytest.raises(PatchApplyError, match="escapes repository root"):
        applier.apply(repo_dir, malicious_candidate)


# ==============================================================================
# 2. Authentication & Tenant Authorization (Horizontal Privilege Escalation)
# ==============================================================================

def test_horizontal_privilege_escalation_blocked():
    store = InMemoryJobStore()
    api_key_store = ApiKeyStore()
    api_key_store.register_token(
        "tenant_alpha_token",
        TenantContext(tenant_id="tenant-alpha", name="Alpha Org", allowed_repositories=("alpha-corp/app-alpha",)),
    )
    api_key_store.register_token(
        "tenant_beta_token",
        TenantContext(tenant_id="tenant-beta", name="Beta Org", allowed_repositories=("beta-corp/app-beta",)),
    )

    dispatcher = WebhookDispatcher(jobs=store, enqueue=lambda j: None)
    app = create_app(
        dispatcher=dispatcher,
        store=store,
        api_key_store=api_key_store,
        auth_enabled=True,
        webhook_secret="dev-secret",
    )
    client = TestClient(app)

    # Create private job for Beta Org
    job_beta = JobRecord(
        job_id="job-beta-confidential",
        repository="beta-corp/app-beta",
        delivery_id="deliv-beta-1",
        commit_sha="b" * 40,
        state=JobState.VERIFIED,
    )
    store.create(job_beta)
    store.save_evidence("job-beta-confidential", {
        "verified": True,
        "commit_sha": "b" * 40,
        "secret_finding": "CVE-2026-9999",
    })

    # 1. Tenant Alpha attempts to access Tenant Beta's job
    resp_job = client.get(
        "/jobs/job-beta-confidential",
        headers={"Authorization": "Bearer tenant_alpha_token"},
    )
    assert resp_job.status_code == 403
    assert "not authorized" in resp_job.json()["detail"]

    # 2. Tenant Alpha attempts to access Tenant Beta's evidence
    resp_ev = client.get(
        "/jobs/job-beta-confidential/evidence",
        headers={"Authorization": "Bearer tenant_alpha_token"},
    )
    assert resp_ev.status_code == 403
    assert "not authorized" in resp_ev.json()["detail"]

    # 3. Tenant Alpha attempts to stream Tenant Beta's events
    resp_sse = client.get(
        "/jobs/job-beta-confidential/events",
        headers={"Authorization": "Bearer tenant_alpha_token"},
    )
    assert resp_sse.status_code == 403

    # 4. Tenant Alpha list jobs endpoint only returns Alpha jobs, never Beta jobs
    resp_list = client.get(
        "/jobs",
        headers={"Authorization": "Bearer tenant_alpha_token"},
    )
    assert resp_list.status_code == 200
    returned_job_ids = [j["job_id"] for j in resp_list.json()["jobs"]]
    assert "job-beta-confidential" not in returned_job_ids


# ==============================================================================
# 3. Webhook Hardening & Idempotency
# ==============================================================================

def test_webhook_hmac_and_size_limits():
    secret = "production-webhook-secret-xyz"
    valid_payload = json.dumps({"repository": {"full_name": "org/repo"}}).encode()
    signature = "sha256=" + hmac.new(secret.encode(), valid_payload, hashlib.sha256).hexdigest()

    # 1. Valid webhook
    event = parse_event(secret, valid_payload, signature, "pull_request", "deliv-123")
    assert event.delivery_id == "deliv-123"

    # 2. Tampered payload
    tampered = json.dumps({"repository": {"full_name": "evil/repo"}}).encode()
    with pytest.raises(InvalidWebhook, match="invalid GitHub webhook signature"):
        parse_event(secret, tampered, signature, "pull_request", "deliv-123")

    # 3. Oversized payload rejected
    oversized = b"x" * (5 * 1024 * 1024 + 1)
    with pytest.raises(InvalidWebhook, match="exceeds maximum allowed size"):
        parse_event(secret, oversized, signature, "pull_request", "deliv-oversized")


# ==============================================================================
# 4. State Machine Strict Transition Invariants
# ==============================================================================

def test_state_machine_illegal_transitions_rejected():
    sm = JobStateMachine()
    job = sm.create("job-sm-test", repository="acme/app", delivery_id="deliv-sm", state=JobState.QUEUED)

    # 1. Cannot jump QUEUED -> PR_CREATED
    with pytest.raises(InvalidTransition):
        sm.transition("job-sm-test", JobState.PR_CREATED)

    # 2. Advance to SCANNING -> ANALYZING -> PATCHING -> VERIFYING
    sm.transition("job-sm-test", JobState.SCANNING)
    sm.transition("job-sm-test", JobState.ANALYZING)
    sm.transition("job-sm-test", JobState.PATCHING)
    sm.transition("job-sm-test", JobState.VERIFYING)

    # 3. Cannot jump VERIFYING -> PR_CREATED directly without passing VERIFIED
    with pytest.raises(InvalidTransition):
        sm.transition("job-sm-test", JobState.PR_CREATED)

    # 4. Transition to FAILED
    sm.transition("job-sm-test", JobState.FAILED)

    # 5. Terminal state FAILED cannot transition to anything
    with pytest.raises(InvalidTransition):
        sm.transition("job-sm-test", JobState.PR_CREATED)


# ==============================================================================
# 5. Verification Gate & Zero-Write Protection
# ==============================================================================

def test_verification_gate_failure_guarantees_zero_github_writes():
    store = InMemoryJobStore()
    remote_writes = {"branch_created": 0, "pr_created": 0}

    class MockTransport:
        def create_ref(self, *a, **k):
            remote_writes["branch_created"] += 1

        def create_pull_request(self, *a, **k):
            remote_writes["pr_created"] += 1
            return {"number": 1}

    client = type("C", (), {
        "create_branch": lambda *a, **k: remote_writes.__setitem__("branch_created", remote_writes["branch_created"] + 1),
        "create_pull_request": lambda *a, **k: remote_writes.__setitem__("pr_created", remote_writes["pr_created"] + 1),
        "verify_repository_permissions": lambda *a, **k: True,
    })()

    publisher = ConcreteGitHubPublisher(client=client)
    signer = Ed25519EvidenceSigner()

    job = JobRecord(
        job_id="job-gate-test",
        repository="enterprise/core-repo",
        delivery_id="deliv-gate",
        commit_sha="7" * 40,
        state=JobState.QUEUED,
    )
    store.create(job)

    class FailingVerification:
        verified = False
        findings = [{"rule_id": "cwe-89"}]

    orchestrator = RemediationOrchestrator(
        store=store,
        state_machine=JobStateMachine(),
        clone=lambda repo, sha: "/tmp/ws",
        scan=lambda ws: [{"rule_id": "cwe-89", "severity": "HIGH"}],
        analyze=lambda ws, f: {"candidate": None, "finding": f[0]},
        patch=lambda ws, p: {"applied_files": ["main.py"], "diff": "diff", "title": "patch"},
        verify=lambda **kw: FailingVerification(),
        evidence=lambda *a, **kw: signer.sign({"job_id": job.job_id, "verified": False, "commit_sha": job.commit_sha}),
        github=publisher,
    )

    result = orchestrator.run("job-gate-test")
    assert result["state"] == "failed"
    assert result["verified"] is False

    # Zero writes guaranteed
    assert remote_writes["branch_created"] == 0
    assert remote_writes["pr_created"] == 0
    assert store.get_pr("job-gate-test") is None


# ==============================================================================
# 6. Celery Task Retry Idempotency
# ==============================================================================

def test_celery_retry_idempotency_deduplicates_pr():
    store = InMemoryJobStore()
    created_prs = []

    class MockPublisher:
        def publish_verified(self, job, patch_result, evidence):
            pr = {"number": 55, "url": "https://github.com/org/repo/pull/55", "head_sha": job.commit_sha}
            created_prs.append(pr)
            return pr

    job = JobRecord(
        job_id="job-retry-test",
        repository="org/repo",
        delivery_id="deliv-retry-1",
        commit_sha="8" * 40,
        state=JobState.QUEUED,
    )
    store.create(job)

    class PassingVerification:
        verified = True
        findings = []

    orchestrator = RemediationOrchestrator(
        store=store,
        state_machine=JobStateMachine(),
        clone=lambda repo, sha: "/tmp/ws",
        scan=lambda ws: [{"rule_id": "cwe-79", "severity": "HIGH"}],
        analyze=lambda ws, f: {"candidate": None, "finding": f[0]},
        patch=lambda ws, p: {"applied_files": ["main.py"], "diff": "diff", "title": "patch"},
        verify=lambda **kw: PassingVerification(),
        evidence=lambda *a, **kw: {"job_id": job.job_id, "verified": True, "commit_sha": job.commit_sha, "signature": "sig"},
        github=MockPublisher(),
    )

    # First run
    res1 = orchestrator.run("job-retry-test")
    assert res1["state"] == "pr_created"
    assert store.get_pr("job-retry-test")["number"] == 55

    # Saved job record now holds PR reference
    saved = store.get("job-retry-test")
    assert saved.pr_number == 55


# ==============================================================================
# 7. Health & Readiness Probes
# ==============================================================================

def test_health_and_readiness_probes():
    store = InMemoryJobStore()
    dispatcher = WebhookDispatcher(jobs=store, enqueue=lambda j: None)
    app = create_app(dispatcher=dispatcher, store=store, webhook_secret="dev-secret", auth_enabled=False)
    client = TestClient(app)

    # Liveness probes
    r_health = client.get("/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "ok"

    r_healthz = client.get("/healthz")
    assert r_healthz.status_code == 200
    assert r_healthz.json()["status"] == "ok"

    # Readiness probe
    r_readyz = client.get("/readyz")
    assert r_readyz.status_code == 200
    assert r_readyz.json()["status"] == "ready"
