import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException

from packages.api.app import create_app
from packages.jobs.state import JobState, JobRecord
from packages.jobs.store import InMemoryJobStore
from packages.webhooks.handlers import WebhookDispatcher
from packages.jobs.celery_app import remediation_task
import packages.jobs.runtime as runtime


@pytest.fixture
def store():
    return InMemoryJobStore()


@pytest.fixture
def mock_enqueue():
    return MagicMock()


@pytest.fixture
def dispatcher(store, mock_enqueue):
    return WebhookDispatcher(jobs=store, enqueue=mock_enqueue)


@pytest.fixture
def client(store, dispatcher):
    app = create_app(dispatcher=dispatcher, store=store, webhook_secret="test-sec", auth_enabled=False)
    return TestClient(app)


def test_async_remediation_trigger_returns_immediately(client, store, mock_enqueue):
    """Test that POST /remediations/run returns immediately with status queued and triggers enqueue."""
    res = client.post(
        "/remediations/run",
        json={
            "repository": "octocat/Hello-World",
            "commit_sha": "main",
            "file": "app.py",
            "start_line": 1,
            "end_line": 2,
            "rule_id": "cwe-89",
            "severity": "HIGH",
            "message": "SQL Injection",
            "auto_create_pr": True,
        },
    )
    assert res.status_code == 200
    data = res.json()
    job_id = data["job_id"]
    assert job_id.startswith("job-")
    assert data["state"] == "queued"
    assert data["verified"] is False

    # Verify JobRecord exists in database store and is queued
    job = store.get(job_id)
    assert job is not None
    assert job.state == JobState.QUEUED

    # Verify enqueue was called with job_id
    mock_enqueue.assert_called_once_with(job_id)


def test_api_enqueue_failure_marks_job_failed(client, store, mock_enqueue):
    """Test that if the background task enqueueing fails, the job transitions to failed."""
    mock_enqueue.side_effect = Exception("Redis connection refused")

    res = client.post(
        "/remediations/run",
        json={
            "repository": "octocat/Hello-World",
            "commit_sha": "main",
            "file": "app.py",
            "start_line": 1,
            "end_line": 2,
            "rule_id": "cwe-89",
            "severity": "HIGH",
            "message": "SQL Injection",
            "auto_create_pr": True,
        },
    )
    assert res.status_code == 500
    assert "Failed to queue remediation task" in res.json()["detail"]

    # Verify that the job record state was updated to FAILED in the database
    jobs = store.list_jobs(repository="octocat/Hello-World")
    assert len(jobs) == 1
    job = jobs[0]
    assert job.state == "failed"
    assert "Enqueue failure" in job.error


@patch("packages.jobs.celery_app._setup_default_worker_orchestrator")
def test_worker_remediation_task_loads_job_and_runs_orchestrator(mock_setup, store):
    """Test that the Celery task remediation_task configures the orchestrator and invokes run()."""
    # Initialize a queued job in store
    job_id = "job-worker-test-123"
    job = JobRecord(
        job_id=job_id,
        delivery_id="delivery-worker-123",
        repository="octocat/Hello-World",
        commit_sha="a" * 40,
        state=JobState.QUEUED,
    )
    store.create(job)

    # Configure a mock orchestrator
    mock_orchestrator = MagicMock()
    mock_orchestrator.run.return_value = {
        "state": JobState.VERIFIED.value,
        "job_id": job_id,
        "verified": True,
    }
    runtime.configure_orchestrator(mock_orchestrator)

    try:
        # Run remediation task synchronously (simulating worker execution)
        result = remediation_task(job_id)

        # Assertions
        mock_orchestrator.run.assert_called_once_with(job_id)
        assert result["state"] == JobState.VERIFIED.value
        assert result["verified"] is True
    finally:
        # Cleanup global runtime config state
        runtime._orchestrator = None


@patch("packages.jobs.celery_app._setup_default_worker_orchestrator")
def test_worker_task_exception_marks_job_failed(mock_setup, store):
    """Test that exceptions raised during worker task execution transition the job to FAILED."""
    job_id = "job-worker-error-123"
    job = JobRecord(
        job_id=job_id,
        delivery_id="delivery-worker-err",
        repository="octocat/Hello-World",
        commit_sha="a" * 40,
        state=JobState.QUEUED,
    )
    store.create(job)

    # Configure a mock orchestrator that raises an exception, with store attached to mock
    mock_orchestrator = MagicMock()
    mock_orchestrator.store = store
    mock_orchestrator.run.side_effect = Exception("gVisor sandbox failed to initialize")
    runtime.configure_orchestrator(mock_orchestrator)

    try:
        # Run task directly and verify it propagates the exception
        with pytest.raises(Exception) as excinfo:
            remediation_task(job_id)
        assert "gVisor sandbox failed" in str(excinfo.value)
        
        # Verify that the crash handler caught it and marked the job failed in the database
        db_job = store.get(job_id)
        assert db_job is not None
        assert db_job.state == JobState.FAILED
        assert "Worker crash" in db_job.error
    finally:
        runtime._orchestrator = None


def test_sse_endpoint_with_async_job(client, store, mock_enqueue):
    """Test that SSE events route functions correctly for async job transition updates."""
    # 1. Trigger the job
    res = client.post(
        "/remediations/run",
        json={
            "repository": "octocat/Hello-World",
            "commit_sha": "main",
            "file": "app.py",
            "start_line": 1,
            "rule_id": "cwe-89",
        },
    )
    job_id = res.json()["job_id"]

    # 2. Add transition events ending in a terminal state to prevent streaming hang
    store.record_transition(job_id, "queued", "scanning", "Beginning scan stage")
    store.record_transition(job_id, "scanning", "failed", "Sandbox compilation failed")
    
    # Update JobRecord state in store to a terminal state
    db_job = store.get(job_id)
    db_job.state = JobState.FAILED
    store.update(db_job)

    # 3. Request events stream
    with client.stream("GET", f"/jobs/{job_id}/events") as response:
        assert response.status_code == 200
        # Read the first event from the chunked stream
        lines = []
        for line in response.iter_lines():
            if line:
                lines.append(line)
            if len(lines) >= 4:
                break
        
        # Verify SSE structure
        content = "".join(lines)
        assert "event: job_state" in content or "event: job_terminal" in content
