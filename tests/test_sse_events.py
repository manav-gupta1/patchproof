import asyncio
import json
import pytest
from fastapi.testclient import TestClient

from packages.api.app import create_app
from packages.auth import ApiKeyStore, TenantContext
from packages.jobs.state import JobRecord, JobState
from packages.jobs.store import InMemoryJobStore
from packages.webhooks.handlers import WebhookDispatcher


@pytest.fixture
def sse_env():
    store = InMemoryJobStore()
    dispatcher = WebhookDispatcher(jobs=store, enqueue=lambda j: None)
    app = create_app(dispatcher=dispatcher, store=store, webhook_secret="dev-secret", auth_enabled=False)
    client = TestClient(app)
    return {"store": store, "client": client, "app": app}


def test_sse_nonexistent_job_returns_404(sse_env):
    client = sse_env["client"]
    resp = client.get("/jobs/job-nonexistent/events")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_sse_tenant_authorization():
    store = InMemoryJobStore()
    api_key_store = ApiKeyStore()
    api_key_store.register_token(
        "tenant_alpha_token",
        TenantContext(tenant_id="tenant-alpha", name="Alpha", allowed_repositories=("alpha-org/repo-a",)),
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

    # Job for beta repo
    job = JobRecord(
        job_id="job-beta-001",
        repository="beta-org/repo-b",
        delivery_id="deliv-b",
        state=JobState.QUEUED,
    )
    store.create(job)

    # 1. Unauthenticated request
    resp_unauth = client.get("/jobs/job-beta-001/events")
    assert resp_unauth.status_code == 401

    # 2. Unauthorized tenant request
    resp_forbidden = client.get(
        "/jobs/job-beta-001/events",
        headers={"Authorization": "Bearer tenant_alpha_token"},
    )
    assert resp_forbidden.status_code == 403
    assert "not authorized" in resp_forbidden.json()["detail"]


def test_sse_streaming_lifecycle_and_reconnection(sse_env):
    store = sse_env["store"]
    client = sse_env["client"]

    job_id = "job-sse-001"
    job = JobRecord(
        job_id=job_id,
        repository="octocat/Hello-World",
        delivery_id="deliv-sse-1",
        commit_sha="a" * 40,
        state=JobState.QUEUED,
    )
    store.create(job)

    # Add transitions
    store.record_transition(job_id, "queued", "scanning", "Cloned source tree")
    store.record_transition(job_id, "scanning", "analyzing", "Identified issue")
    store.record_transition(job_id, "analyzing", "patching", "Applied AST patch")
    store.record_transition(job_id, "patching", "verifying", "Sandbox execution")
    store.record_transition(job_id, "verifying", "verified", "Verification passed")
    store.record_transition(job_id, "verified", "pr_created", "Created PR #42")

    store.save_pr(job_id, {
        "number": 42,
        "url": "https://github.com/octocat/Hello-World/pull/42",
        "head_sha": "a" * 40,
        "branch": "patchproof/fix",
    })

    # Read SSE stream
    with client.stream("GET", f"/jobs/{job_id}/events") as resp:
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]

        lines = [line for line in resp.iter_lines() if line]
        # Filter for data lines
        data_lines = [l for l in lines if l.startswith("data: ")]
        assert len(data_lines) >= 7  # Initial + 6 transitions + terminal

        # Check initial event
        first_event = json.loads(data_lines[0].replace("data: ", ""))
        assert first_event["job_id"] == job_id
        assert first_event["to_state"] == "queued"

        # Check terminal event
        terminal_event = json.loads(data_lines[-1].replace("data: ", ""))
        assert terminal_event["job_id"] == job_id
        assert terminal_event["state"] == "pr_created"
        assert terminal_event["pr_number"] == 42


def test_sse_reconnect_with_last_event_id(sse_env):
    store = sse_env["store"]
    client = sse_env["client"]

    job_id = "job-sse-reconnect-002"
    job = JobRecord(
        job_id=job_id,
        repository="octocat/Hello-World",
        delivery_id="deliv-sse-2",
        commit_sha="b" * 40,
        state=JobState.QUEUED,
    )
    store.create(job)

    store.record_transition(job_id, "queued", "scanning", "Scan 1")
    store.record_transition(job_id, "scanning", "analyzing", "Analyze 2")
    store.record_transition(job_id, "analyzing", "patching", "Patch 3")
    store.record_transition(job_id, "patching", "verifying", "Verify 4")
    store.record_transition(job_id, "verifying", "verified", "Verified 5")
    store.record_transition(job_id, "verified", "pr_created", "PR 6")

    # Reconnect asking only for events after event ID 4
    with client.stream("GET", f"/jobs/{job_id}/events", headers={"Last-Event-ID": "4"}) as resp:
        assert resp.status_code == 200
        lines = [line for line in resp.iter_lines() if line]
        data_lines = [l for l in lines if l.startswith("data: ")]

        # Should only receive event 5, 6, 7 and terminal
        events = [json.loads(l.replace("data: ", "")) for l in data_lines]
        event_ids = [e.get("event_id") for e in events if "event_id" in e]
        assert all(eid > 4 for eid in event_ids)


def test_sse_failed_terminal_flow(sse_env):
    store = sse_env["store"]
    client = sse_env["client"]

    job_id = "job-sse-fail-003"
    job = JobRecord(
        job_id=job_id,
        repository="acme/vulnerable-app",
        delivery_id="deliv-sse-3",
        commit_sha="c" * 40,
        state=JobState.QUEUED,
    )
    store.create(job)

    store.record_transition(job_id, "queued", "scanning", "Scan")
    store.record_transition(job_id, "scanning", "verifying", "Running tests in gVisor")
    store.record_transition(job_id, "verifying", "failed", "Verification failed: pytest returned exit code 1")

    with client.stream("GET", f"/jobs/{job_id}/events") as resp:
        assert resp.status_code == 200
        lines = [line for line in resp.iter_lines() if line]
        data_lines = [l for l in lines if l.startswith("data: ")]

        terminal_event = json.loads(data_lines[-1].replace("data: ", ""))
        assert terminal_event["job_id"] == job_id
        assert terminal_event["state"] == "failed"
        assert "pytest returned exit code 1" in terminal_event["error"]


def test_sse_secret_redaction(sse_env):
    store = sse_env["store"]
    client = sse_env["client"]

    job_id = "job-sse-secret-004"
    job = JobRecord(
        job_id=job_id,
        repository="acme/secret-app",
        delivery_id="deliv-sse-4",
        commit_sha="d" * 40,
        state=JobState.QUEUED,
    )
    store.create(job)

    # Transition with leaked secret string
    store.record_transition(
        job_id,
        "queued",
        "failed",
        "Failed with token ghp_1234567890abcdef1234567890abcdef1234 and key -----BEGIN RSA PRIVATE KEY----- SECRET -----END RSA PRIVATE KEY-----",
    )

    with client.stream("GET", f"/jobs/{job_id}/events") as resp:
        assert resp.status_code == 200
        content = resp.read().decode()
        assert "ghp_1234567890abcdef1234567890abcdef1234" not in content
        assert "-----BEGIN RSA PRIVATE KEY-----" not in content
        assert "[REDACTED_SECRET]" in content or "[REDACTED_PRIVATE_KEY]" in content or "[REDACTED" in content


def test_tenant_wide_events_stream(sse_env):
    store = sse_env["store"]
    client = sse_env["client"]

    job_id = "job-tenant-stream-01"
    job = JobRecord(
        job_id=job_id,
        repository="octocat/Hello-World",
        delivery_id="deliv-tenant-1",
        commit_sha="c" * 40,
        state=JobState.QUEUED,
    )
    store.create(job)
    store.record_transition(job_id, "queued", "scanning", "Started scan")
    store.record_transition(job_id, "scanning", "verified", "Verification passed")

    with client.stream("GET", "/events?limit=2") as resp:
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        lines = [line for line in resp.iter_lines() if line]
        data_lines = [l for l in lines if l.startswith("data: ")]
        assert len(data_lines) >= 1
        first_ev = json.loads(data_lines[0].replace("data: ", ""))
        assert first_ev["job_id"] == job_id
        assert "to_state" in first_ev
