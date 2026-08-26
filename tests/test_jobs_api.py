import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from packages.api.app import create_app
from packages.jobs.state import JobState, JobRecord
from packages.jobs.store import InMemoryJobStore
from packages.webhooks.handlers import WebhookDispatcher


@pytest.fixture
def store():
    return InMemoryJobStore()


@pytest.fixture
def client(store):
    dispatcher = WebhookDispatcher(jobs=store, enqueue=lambda job_id: None)
    app = create_app(dispatcher=dispatcher, store=store, webhook_secret="test-webhook-secret", auth_enabled=False)
    return TestClient(app)


def test_job_not_found_returns_404(client):
    """Test that querying a non-existent job ID returns 404 with a structured error."""
    resp = client.get("/jobs/non-existent-job-12345")
    assert resp.status_code == 404
    data = resp.json()
    assert "Job 'non-existent-job-12345' not found" in data["detail"]


def test_get_job_status_queued_state(client, store):
    """Test getting status for a newly created queued job."""
    job = JobRecord(
        job_id="job-test-queued-001",
        repository="octocat/Hello-World",
        delivery_id="delivery-001",
        commit_sha="a" * 40,
        state=JobState.QUEUED,
    )
    job.event_type = "pull_request"
    store.create(job)

    resp = client.get(f"/jobs/{job.job_id}")
    assert resp.status_code == 200
    data = resp.json()

    assert data["job_id"] == "job-test-queued-001"
    assert data["repository"] == "octocat/Hello-World"
    assert data["commit_sha"] == "a" * 40
    assert data["event_type"] == "pull_request"
    assert data["state"] == "queued"
    assert data["verified"] is None
    assert data["pr"] is None
    assert data["error"] is None
    assert len(data["events"]) >= 1
    assert data["events"][0]["to_state"] == "queued"


def test_get_job_status_full_lifecycle_transitions(client, store):
    """Test full lifecycle transition history returned in chronological order."""
    job_id = "job-lifecycle-001"
    job = JobRecord(
        job_id=job_id,
        repository="acme/security-test",
        delivery_id="deliv-lifecycle",
        commit_sha="b" * 40,
        state=JobState.QUEUED,
    )
    store.create(job)

    store.record_transition(job_id, "queued", "scanning", "source checkout complete")
    store.record_transition(job_id, "scanning", "analyzing", "security findings collected")
    store.record_transition(job_id, "analyzing", "patching", "remediation proposal generated")
    store.record_transition(job_id, "patching", "verifying", "patch applied; verification started")
    store.record_transition(job_id, "verifying", "verified", "verification passed")
    store.record_transition(job_id, "verified", "pr_created", "verified remediation PR created")

    store.save_pr(job_id, {
        "number": 42,
        "url": "https://github.com/acme/security-test/pull/42",
        "head_sha": "b" * 40,
        "branch": "patchproof/fix-sqli",
        "base_branch": "main",
        "repository": "acme/security-test",
    })

    resp = client.get(f"/jobs/{job_id}")
    assert resp.status_code == 200
    data = resp.json()

    assert data["state"] == "pr_created"
    assert data["verified"] is True
    assert data["pr"]["number"] == 42
    assert data["pr"]["url"] == "https://github.com/acme/security-test/pull/42"
    assert data["pr"]["branch"] == "patchproof/fix-sqli"
    assert data["pr"]["base_branch"] == "main"

    # Verify event transitions sequence
    states = [e["to_state"] for e in data["events"]]
    assert states == ["queued", "scanning", "analyzing", "patching", "verifying", "verified", "pr_created"]


def test_get_job_status_failed_job(client, store):
    """Test getting status for a failed job with sanitized error diagnostics."""
    job_id = "job-failed-001"
    job = JobRecord(
        job_id=job_id,
        repository="acme/failing-app",
        delivery_id="deliv-failed",
        commit_sha="c" * 40,
        state=JobState.QUEUED,
    )
    store.create(job)
    store.record_transition(job_id, "queued", "scanning", "started scan")
    store.record_transition(
        job_id,
        "scanning",
        "failed",
        "Scan failed with token ghs_secret_token_1234567890 at https://x-access-token:ghs_secret@github.com/acme/failing-app",
    )

    resp = client.get(f"/jobs/{job_id}")
    assert resp.status_code == 200
    data = resp.json()

    assert data["state"] == "failed"
    assert data["verified"] is False
    assert data["pr"] is None
    assert "Scan failed" in data["error"]
    # Verify secret is redacted
    assert "ghs_secret_token_1234567890" not in data["error"]
    assert "[REDACTED_TOKEN]" in data["error"] or "[REDACTED" in data["error"]


def test_get_job_evidence_missing_returns_404(client, store):
    """Test that querying evidence for a job before evidence is generated returns 404."""
    job_id = "job-no-evidence-001"
    job = JobRecord(
        job_id=job_id,
        repository="acme/test",
        delivery_id="deliv-no-ev",
        commit_sha="d" * 40,
        state=JobState.QUEUED,
    )
    store.create(job)

    resp = client.get(f"/jobs/{job_id}/evidence")
    assert resp.status_code == 404
    data = resp.json()
    assert f"Verification evidence for job '{job_id}' is not available" in data["detail"]


def test_get_job_evidence_success(client, store):
    """Test retrieving structured verification evidence bundle."""
    job_id = "job-evidence-success-001"
    job = JobRecord(
        job_id=job_id,
        repository="acme/target-repo",
        delivery_id="deliv-ev-success",
        commit_sha="e" * 40,
        state=JobState.PR_CREATED,
    )
    store.create(job)

    evidence_data = {
        "evidence_id": f"ev-{job_id}",
        "job_id": job_id,
        "commit_sha": "e" * 40,
        "repository": "acme/target-repo",
        "verified": True,
        "finding_count": 1,
        "target_finding": {
            "rule_id": "python.lang.security.injection.sql-injection",
            "fingerprint": "fp-sqli-9988",
            "severity": "HIGH",
        },
        "verification_results": {
            "rescan_findings_count": 0,
            "target_vulnerability_eliminated": True,
            "verification_status": "passed",
            "test_summary": "Passed exploit proof and re-scan tests.",
        },
        "patch_summary": {
            "title": "fix(security): parameterize SQL query",
            "files_changed": ["app.py"],
            "head_branch": "patchproof/fp-sqli-9988",
            "base_branch": "main",
            "explanation": "Replaced f-string string interpolation with parameterized cursor execution.",
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    store.save_evidence(job_id, evidence_data)
    store.save_pr(job_id, {
        "number": 15,
        "url": "https://github.com/acme/target-repo/pull/15",
        "head_sha": "e" * 40,
        "branch": "patchproof/fp-sqli-9988",
        "base_branch": "main",
    })

    resp = client.get(f"/jobs/{job_id}/evidence")
    assert resp.status_code == 200
    data = resp.json()

    assert data["evidence_id"] == f"ev-{job_id}"
    assert data["job_id"] == job_id
    assert data["commit_sha"] == "e" * 40
    assert data["repository"] == "acme/target-repo"
    assert data["verified"] is True
    assert data["finding_count"] == 1
    assert data["target_finding"]["rule_id"] == "python.lang.security.injection.sql-injection"
    assert data["target_finding"]["fingerprint"] == "fp-sqli-9988"
    assert data["verification_results"]["rescan_findings_count"] == 0
    assert data["verification_results"]["target_vulnerability_eliminated"] is True
    assert data["patch_summary"]["title"] == "fix(security): parameterize SQL query"
    assert data["patch_summary"]["files_changed"] == ["app.py"]
    assert data["pr"]["number"] == 15
    assert data["pr"]["url"] == "https://github.com/acme/target-repo/pull/15"


def test_evidence_secret_redaction(client, store):
    """Test that credentials in evidence explanations or summaries are redacted."""
    job_id = "job-ev-secret-001"
    job = JobRecord(
        job_id=job_id,
        repository="acme/secret-test",
        delivery_id="deliv-sec-ev",
        commit_sha="f" * 40,
        state=JobState.VERIFIED,
    )
    store.create(job)

    evidence_data = {
        "evidence_id": f"ev-{job_id}",
        "job_id": job_id,
        "commit_sha": "f" * 40,
        "repository": "acme/secret-test",
        "verified": True,
        "finding_count": 1,
        "verification_results": {
            "test_summary": "Passed with token ghs_test_token_123456789012345678",
        },
        "patch_summary": {
            "explanation": "Applied with Bearer eyJhbGciOiJSUzI1NiJ9.test.jwt",
        },
    }
    store.save_evidence(job_id, evidence_data)

    resp = client.get(f"/jobs/{job_id}/evidence")
    assert resp.status_code == 200
    data = resp.json()

    assert "ghs_test_token_123456789012345678" not in data["verification_results"]["test_summary"]
    assert "[REDACTED_TOKEN]" in data["verification_results"]["test_summary"]
    assert "Bearer [REDACTED_JWT]" in data["patch_summary"]["explanation"]


def test_openapi_schema_contains_new_endpoints(client):
    """Test that OpenAPI schema properly registers /jobs/{job_id} and /jobs/{job_id}/evidence."""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()

    paths = schema.get("paths", {})
    assert "/jobs/{job_id}" in paths
    assert "get" in paths["/jobs/{job_id}"]
    assert "/jobs/{job_id}/evidence" in paths
    assert "get" in paths["/jobs/{job_id}/evidence"]

    schemas = schema.get("components", {}).get("schemas", {})
    assert "JobStatusResponse" in schemas
    assert "JobEvidenceResponse" in schemas
    assert "JobEventResponse" in schemas
    assert "PullRequestInfo" in schemas
