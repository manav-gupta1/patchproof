import hashlib
import hmac
import json
import pytest
from fastapi.testclient import TestClient

from packages.api.app import create_app
from packages.auth import ApiKeyStore, TenantContext, hash_api_token
from packages.jobs.state import JobRecord, JobState
from packages.jobs.store import InMemoryJobStore
from packages.webhooks.handlers import WebhookDispatcher


@pytest.fixture
def store():
    return InMemoryJobStore()


@pytest.fixture
def auth_store():
    store = ApiKeyStore()
    # Tenant 1: Acme Corp (owns acme/*)
    store.register_token(
        "token-acme-secret-12345",
        TenantContext(
            tenant_id="tenant-acme",
            name="Acme Corp",
            allowed_repositories=("acme/*", "example/allowed-repo"),
            is_admin=False,
        ),
    )
    # Tenant 2: Globex Corp (owns globex/*)
    store.register_token(
        "token-globex-secret-67890",
        TenantContext(
            tenant_id="tenant-globex",
            name="Globex Corp",
            allowed_repositories=("globex/*",),
            is_admin=False,
        ),
    )
    # Tenant 3: System Admin
    store.register_token(
        "token-admin-master-99999",
        TenantContext(
            tenant_id="tenant-admin",
            name="System Administrator",
            allowed_repositories=("*",),
            is_admin=True,
        ),
    )
    return store


@pytest.fixture
def auth_client(store, auth_store):
    dispatcher = WebhookDispatcher(jobs=store, enqueue=lambda job_id: None)
    app = create_app(
        dispatcher=dispatcher,
        store=store,
        webhook_secret="test-webhook-secret",
        auth_enabled=True,
        api_key_store=auth_store,
    )
    return TestClient(app)


def test_missing_authorization_header_returns_401(auth_client, store):
    """Test that requests to /jobs/{job_id} without auth header are rejected with 401."""
    job = JobRecord(
        job_id="job-auth-001",
        repository="acme/service",
        delivery_id="deliv-1",
        commit_sha="a" * 40,
        state=JobState.QUEUED,
    )
    store.create(job)

    resp = auth_client.get(f"/jobs/{job.job_id}")
    assert resp.status_code == 401
    assert "Missing Authorization header" in resp.json()["detail"]
    assert "Bearer" in resp.headers.get("www-authenticate", "")


def test_malformed_authorization_header_returns_401(auth_client, store):
    """Test that malformed Authorization headers (e.g. 3 parts) return 401."""
    resp = auth_client.get(
        "/jobs/job-auth-001",
        headers={"Authorization": "Bearer too many parts in token header"},
    )
    assert resp.status_code == 401
    assert "Invalid Authorization header format" in resp.json()["detail"]


def test_invalid_token_returns_401(auth_client, store):
    """Test that invalid/unregistered tokens return 401."""
    resp = auth_client.get(
        "/jobs/job-auth-001",
        headers={"Authorization": "Bearer token-invalid-wrong-999"},
    )
    assert resp.status_code == 401
    assert "Invalid or expired API token" in resp.json()["detail"]


def test_valid_token_authorized_tenant_access(auth_client, store):
    """Test that an authorized tenant can access jobs in its allowed repositories."""
    job = JobRecord(
        job_id="job-acme-001",
        repository="acme/api-service",
        delivery_id="deliv-acme",
        commit_sha="b" * 40,
        state=JobState.QUEUED,
    )
    store.create(job)

    # Acme accesses its own job
    resp = auth_client.get(
        f"/jobs/{job.job_id}",
        headers={"Authorization": "Bearer token-acme-secret-12345"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == "job-acme-001"
    assert data["repository"] == "acme/api-service"


def test_x_api_key_header_authentication(auth_client, store):
    """Test that X-API-Key header can also be used for authentication."""
    job = JobRecord(
        job_id="job-acme-002",
        repository="acme/web-app",
        delivery_id="deliv-x-key",
        commit_sha="c" * 40,
        state=JobState.QUEUED,
    )
    store.create(job)

    resp = auth_client.get(
        f"/jobs/{job.job_id}",
        headers={"X-API-Key": "token-acme-secret-12345"},
    )
    assert resp.status_code == 200
    assert resp.json()["job_id"] == "job-acme-002"


def test_cross_tenant_job_access_is_forbidden(auth_client, store):
    """Test IDOR prevention: Globex tenant attempts to access Acme job and is rejected with 403."""
    job = JobRecord(
        job_id="job-acme-confidential",
        repository="acme/internal-payments",
        delivery_id="deliv-secret",
        commit_sha="d" * 40,
        state=JobState.QUEUED,
    )
    store.create(job)

    # Globex token querying Acme job
    resp = auth_client.get(
        f"/jobs/{job.job_id}",
        headers={"Authorization": "Bearer token-globex-secret-67890"},
    )
    assert resp.status_code == 403
    data = resp.json()
    assert "Tenant 'tenant-globex' is not authorized" in data["detail"]
    assert "acme/internal-payments" in data["detail"]


def test_cross_tenant_evidence_access_is_forbidden(auth_client, store):
    """Test IDOR prevention on /jobs/{job_id}/evidence: unauthorized tenant is rejected with 403."""
    job_id = "job-acme-evidence-sec"
    job = JobRecord(
        job_id=job_id,
        repository="acme/vault",
        delivery_id="deliv-vault",
        commit_sha="e" * 40,
        state=JobState.VERIFIED,
    )
    store.create(job)
    store.save_evidence(job_id, {
        "evidence_id": "ev-acme-vault",
        "job_id": job_id,
        "commit_sha": "e" * 40,
        "repository": "acme/vault",
        "verified": True,
    })

    # Globex token querying Acme evidence
    resp = auth_client.get(
        f"/jobs/{job_id}/evidence",
        headers={"Authorization": "Bearer token-globex-secret-67890"},
    )
    assert resp.status_code == 403
    assert "Tenant 'tenant-globex' is not authorized" in resp.json()["detail"]


def test_admin_tenant_can_access_all_repositories(auth_client, store):
    """Test that admin tenant with '*' scope can access jobs across all repositories."""
    job1 = JobRecord(job_id="job-acme-adm", repository="acme/core", delivery_id="d1", commit_sha="1"*40, state=JobState.QUEUED)
    job2 = JobRecord(job_id="job-globex-adm", repository="globex/core", delivery_id="d2", commit_sha="2"*40, state=JobState.QUEUED)
    store.create(job1)
    store.create(job2)

    # Admin accesses Acme job
    resp1 = auth_client.get(
        f"/jobs/{job1.job_id}",
        headers={"Authorization": "Bearer token-admin-master-99999"},
    )
    assert resp1.status_code == 200

    # Admin accesses Globex job
    resp2 = auth_client.get(
        f"/jobs/{job2.job_id}",
        headers={"Authorization": "Bearer token-admin-master-99999"},
    )
    assert resp2.status_code == 200


def test_health_endpoints_accessible_without_auth(auth_client):
    """Test that /health, /healthz, and /readyz do not require authentication."""
    assert auth_client.get("/health").status_code == 200
    assert auth_client.get("/healthz").status_code == 200
    assert auth_client.get("/readyz").status_code == 200


def test_webhook_ingestion_works_without_rest_bearer_token(auth_client):
    """Test that GitHub webhook endpoint works with HMAC signature and without REST bearer auth."""
    secret = "test-webhook-secret"
    payload = json.dumps({
        "action": "opened",
        "pull_request": {
            "number": 10,
            "head": {"sha": "f" * 40, "ref": "feat"},
            "base": {"sha": "0" * 40, "ref": "main"},
        },
        "repository": {
            "full_name": "acme/repo",
            "name": "repo",
            "owner": {"login": "acme"},
        },
    }).encode("utf-8")

    sig = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

    resp = auth_client.post(
        "/webhooks/github",
        content=payload,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": sig,
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "deliv-webhook-auth-001",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["accepted"] is True


def test_auth_store_env_loading(monkeypatch):
    """Test loading ApiKeyStore from environment variables (PATCHPROOF_API_KEY and PATCHPROOF_API_KEYS)."""
    monkeypatch.setenv("PATCHPROOF_API_KEY", "env-single-key-12345")
    store = ApiKeyStore.from_env()

    tenant = store.authenticate_token("env-single-key-12345")
    assert tenant is not None
    assert tenant.tenant_id == "default-tenant"
    assert tenant.can_access_repository("any/repo") is True

    # JSON multi-tenant config
    multi_json = json.dumps({
        "key-corp-a": {
            "tenant_id": "corp-a",
            "name": "Corp A",
            "allowed_repositories": ["corp-a/*"],
        },
        "key-corp-b": {
            "tenant_id": "corp-b",
            "name": "Corp B",
            "allowed_repositories": ["corp-b/app"],
        },
    })
    monkeypatch.setenv("PATCHPROOF_API_KEYS", multi_json)
    store2 = ApiKeyStore.from_env()

    tenant_a = store2.authenticate_token("key-corp-a")
    assert tenant_a is not None
    assert tenant_a.tenant_id == "corp-a"
    assert tenant_a.can_access_repository("corp-a/service") is True
    assert tenant_a.can_access_repository("corp-b/app") is False

    tenant_b = store2.authenticate_token("key-corp-b")
    assert tenant_b is not None
    assert tenant_b.can_access_repository("corp-b/app") is True
    assert tenant_b.can_access_repository("corp-b/other") is False
