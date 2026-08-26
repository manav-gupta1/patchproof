import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from packages.api.app import create_app
from packages.jobs.state import JobState, JobRecord
from packages.jobs.store import InMemoryJobStore
from packages.webhooks.handlers import WebhookDispatcher
from packages.auth import ApiKeyStore, TenantContext


@pytest.fixture
def store():
    return InMemoryJobStore()


@pytest.fixture
def client(store):
    dispatcher = WebhookDispatcher(jobs=store, enqueue=lambda job_id: None)
    app = create_app(
        dispatcher=dispatcher,
        store=store,
        webhook_secret="test-webhook-secret",
        auth_enabled=False,
    )
    return TestClient(app)


def test_list_jobs_empty(client):
    resp = client.get("/jobs")
    assert resp.status_code == 200
    data = resp.json()
    assert data["jobs"] == []
    assert data["total"] == 0


def test_list_jobs_with_filtering_and_pagination(client, store):
    job1 = JobRecord(
        job_id="job-gui-001",
        repository="org/repo-a",
        delivery_id="deliv-001",
        commit_sha="a" * 40,
        state=JobState.VERIFIED,
    )
    job2 = JobRecord(
        job_id="job-gui-002",
        repository="org/repo-b",
        delivery_id="deliv-002",
        commit_sha="b" * 40,
        state=JobState.FAILED,
    )
    store.create(job1)
    store.create(job2)

    # All jobs
    resp = client.get("/jobs")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["jobs"]) == 2

    # Filter by repo
    resp_repo = client.get("/jobs?repository=org/repo-a")
    assert resp_repo.status_code == 200
    data_repo = resp_repo.json()
    assert data_repo["total"] == 1
    assert data_repo["jobs"][0]["job_id"] == "job-gui-001"

    # Filter by state
    resp_state = client.get("/jobs?state=failed")
    assert resp_state.status_code == 200
    data_state = resp_state.json()
    assert data_state["total"] == 1
    assert data_state["jobs"][0]["job_id"] == "job-gui-002"


def test_list_repositories(client, store):
    job1 = JobRecord(
        job_id="job-gui-101",
        repository="org/backend",
        delivery_id="deliv-101",
        commit_sha="1" * 40,
        state=JobState.PR_CREATED,
    )
    job2 = JobRecord(
        job_id="job-gui-102",
        repository="org/backend",
        delivery_id="deliv-102",
        commit_sha="2" * 40,
        state=JobState.FAILED,
    )
    store.create(job1)
    store.create(job2)

    resp = client.get("/repositories")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    repo = next(r for r in data["repositories"] if r["repository"] == "org/backend")
    assert repo["total_jobs"] == 2
    assert repo["verified_prs"] == 1
    assert repo["failed_jobs"] == 1


def test_system_status(client):
    resp = client.get("/system/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["api"] == "healthy"
    assert data["database"] in {"healthy", "degraded"}
    assert data["sandbox"]["provider"] == "gVisor"
    assert data["sandbox"]["network_policy"] == "deny"
    assert data["sandbox"]["isolated"] is True


def test_settings_status(client):
    resp = client.get("/settings/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["webhook_configured"] is True
    assert data["evidence_signing"]["configured"] is True
    assert data["evidence_signing"]["algorithm"] == "ed25519"
    assert "private" not in str(data).lower()
