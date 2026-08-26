from __future__ import annotations

import tempfile
import os
from fastapi.testclient import TestClient

from packages.api.app import create_app
from packages.auth import ApiKeyStore, TenantContext
from packages.jobs.store import InMemoryJobStore
from packages.store.postgres import PostgresJobStore
from packages.webhooks.handlers import WebhookDispatcher


def test_repository_policy_crud_and_validation():
    store = InMemoryJobStore()
    api_key_store = ApiKeyStore()
    api_key_store.register_token(
        "tenant_token",
        TenantContext(tenant_id="tenant-1", name="Acme Corp", allowed_repositories=("acme/app",)),
    )

    dispatcher = WebhookDispatcher(jobs=store, enqueue=lambda j: None)
    app = create_app(
        dispatcher=dispatcher,
        store=store,
        api_key_store=api_key_store,
        auth_enabled=True,
        webhook_secret="test-secret",
    )
    client = TestClient(app)

    # 1. Get default policy
    resp_get = client.get(
        "/repositories/acme/app/policy",
        headers={"Authorization": "Bearer tenant_token"},
    )
    assert resp_get.status_code == 200
    data_get = resp_get.json()
    assert data_get["repository"] == "acme/app"
    assert data_get["minimum_severity"] == "medium"
    assert data_get["auto_remediate"] is True

    # 2. Update policy with custom rules
    new_policy = {
        "enabled": True,
        "minimum_severity": "high",
        "auto_remediate": True,
        "auto_create_pr": True,
        "target_branches": ["main", "release/*"],
    }
    resp_put = client.put(
        "/repositories/acme/app/policy",
        json=new_policy,
        headers={"Authorization": "Bearer tenant_token"},
    )
    assert resp_put.status_code == 200
    data_put = resp_put.json()
    assert data_put["minimum_severity"] == "high"
    assert "release/*" in data_put["target_branches"]

    # 3. Retrieve updated policy
    resp_get_updated = client.get(
        "/repositories/acme/app/policy",
        headers={"Authorization": "Bearer tenant_token"},
    )
    assert resp_get_updated.status_code == 200
    assert resp_get_updated.json()["minimum_severity"] == "high"

    # 4. Reject invalid minimum_severity
    resp_invalid = client.put(
        "/repositories/acme/app/policy",
        json={"minimum_severity": "super_critical_invalid"},
        headers={"Authorization": "Bearer tenant_token"},
    )
    assert resp_invalid.status_code == 400
    assert "Invalid minimum_severity" in resp_invalid.json()["detail"]

    # 5. Reject invalid target_branches (empty list)
    resp_invalid_branches = client.put(
        "/repositories/acme/app/policy",
        json={"target_branches": []},
        headers={"Authorization": "Bearer tenant_token"},
    )
    assert resp_invalid_branches.status_code == 400
    assert "target_branches must contain at least one" in resp_invalid_branches.json()["detail"]

    # 6. Reject invalid allowed_events
    resp_invalid_events = client.put(
        "/repositories/acme/app/policy",
        json={"allowed_events": ["invalid_event_xyz"]},
        headers={"Authorization": "Bearer tenant_token"},
    )
    assert resp_invalid_events.status_code == 400
    assert "Invalid event" in resp_invalid_events.json()["detail"]


def test_repository_policy_tenant_isolation():
    store = InMemoryJobStore()
    api_key_store = ApiKeyStore()
    api_key_store.register_token(
        "tenant_alpha",
        TenantContext(tenant_id="alpha", name="Alpha", allowed_repositories=("alpha/repo",)),
    )

    dispatcher = WebhookDispatcher(jobs=store, enqueue=lambda j: None)
    app = create_app(
        dispatcher=dispatcher,
        store=store,
        api_key_store=api_key_store,
        auth_enabled=True,
        webhook_secret="test-secret",
    )
    client = TestClient(app)

    # Attempt to read Beta's repo policy
    resp = client.get(
        "/repositories/beta/repo/policy",
        headers={"Authorization": "Bearer tenant_alpha"},
    )
    assert resp.status_code == 403
    assert "not authorized" in resp.json()["detail"]


def test_postgres_repository_policy_persistence_and_isolation():
    """Verify PostgresJobStore persists repository policies across store instances and respects repo boundaries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_policy.db")
        db_url = f"sqlite:///{db_path}"

        # Initialize store 1 and create schema
        store1 = PostgresJobStore(db_url)
        store1.create_schema()

        api_key_store = ApiKeyStore()
        api_key_store.register_token(
            "test_token",
            TenantContext(
                tenant_id="test-tenant",
                name="Test Tenant",
                allowed_repositories=("octocat/hello-world", "octocat/other-repo"),
            ),
        )

        dispatcher1 = WebhookDispatcher(jobs=store1, enqueue=lambda j: None)
        app1 = create_app(
            dispatcher=dispatcher1,
            store=store1,
            api_key_store=api_key_store,
            auth_enabled=True,
            webhook_secret="test-secret",
        )
        client1 = TestClient(app1)

        # 1. Update policy for octocat/hello-world
        put_payload = {
            "enabled": True,
            "minimum_severity": "critical",
            "auto_remediate": False,
            "auto_create_pr": True,
            "target_branches": ["main", "prod"],
            "allowed_events": ["pull_request", "check_run"],
        }
        res_put = client1.put(
            "/repositories/octocat/hello-world/policy",
            json=put_payload,
            headers={"Authorization": "Bearer test_token"},
        )
        assert res_put.status_code == 200
        assert res_put.json()["minimum_severity"] == "critical"
        assert res_put.json()["auto_remediate"] is False

        # 2. Simulate server restart / fresh connection with new PostgresJobStore instance
        store2 = PostgresJobStore(db_url)
        dispatcher2 = WebhookDispatcher(jobs=store2, enqueue=lambda j: None)
        app2 = create_app(
            dispatcher=dispatcher2,
            store=store2,
            api_key_store=api_key_store,
            auth_enabled=True,
            webhook_secret="test-secret",
        )
        client2 = TestClient(app2)

        # 3. GET on the new instance returns persisted policy values
        res_get = client2.get(
            "/repositories/octocat/hello-world/policy",
            headers={"Authorization": "Bearer test_token"},
        )
        assert res_get.status_code == 200
        persisted = res_get.json()
        assert persisted["repository"] == "octocat/hello-world"
        assert persisted["minimum_severity"] == "critical"
        assert persisted["auto_remediate"] is False
        assert persisted["target_branches"] == ["main", "prod"]

        # 4. Proving saving octocat/hello-world did not affect octocat/other-repo
        res_other = client2.get(
            "/repositories/octocat/other-repo/policy",
            headers={"Authorization": "Bearer test_token"},
        )
        assert res_other.status_code == 200
        other_policy = res_other.json()
        assert other_policy["minimum_severity"] == "medium"  # default
        assert other_policy["auto_remediate"] is True  # default
