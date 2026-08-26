import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from packages.api.app import create_app
from packages.jobs.state import JobState, JobRecord
from packages.jobs.store import InMemoryJobStore
from packages.webhooks.handlers import WebhookDispatcher
from packages.signing import Ed25519EvidenceSigner, verify_evidence


@pytest.fixture
def e2e_env():
    store = InMemoryJobStore()
    dispatcher = WebhookDispatcher(jobs=store, enqueue=lambda job_id: None)
    app = create_app(
        dispatcher=dispatcher,
        store=store,
        webhook_secret="test-webhook-secret",
        auth_enabled=False,
    )
    client = TestClient(app)
    return {"store": store, "client": client, "dispatcher": dispatcher}


def test_complete_e2e_successful_remediation_gui_flow(e2e_env):
    store = e2e_env["store"]
    client = e2e_env["client"]

    # 1. Simulate GitHub Webhook creating remediation job
    job_id = "job-e2e-success-001"
    repo = "patchproof-org/vulnerable-app"
    commit_sha = "d14a028c2a3a2bc9476102bb288234c415a2b01f"

    job = JobRecord(
        job_id=job_id,
        repository=repo,
        delivery_id="deliv-e2e-001",
        commit_sha=commit_sha,
        state=JobState.QUEUED,
    )
    job.event_type = "pull_request"
    job.target_branch = "main"
    store.create(job)

    # 2. Verify job appears in Dashboard / Jobs list
    res_jobs = client.get("/jobs")
    assert res_jobs.status_code == 200
    data_jobs = res_jobs.json()
    assert data_jobs["total"] == 1
    assert data_jobs["jobs"][0]["job_id"] == job_id
    assert data_jobs["jobs"][0]["state"] == "queued"

    # 3. Simulate Worker transitions through lifecycle
    store.record_transition(job_id, "queued", "scanning", "Cloned source repository")
    store.record_transition(job_id, "scanning", "analyzing", "Semgrep detected CWE-89 SQL Injection")
    store.record_transition(job_id, "analyzing", "patching", "Synthesized parameterized query patch")
    store.record_transition(job_id, "patching", "verifying", "Running exploit reproduction & test suite in gVisor")
    store.record_transition(job_id, "verifying", "verified", "Vulnerability eliminated, zero regressions, 100% test pass")
    store.record_transition(job_id, "verified", "pr_created", "Created GitHub Pull Request #42")

    # 4. Save Policy Decision
    policy_decision = {
        "allowed": True,
        "action": "remediate_and_publish",
        "reason": "Vulnerability is HIGH severity and matches auto_create_pr policy.",
        "target_branch": "main",
        "auto_create_pr": True,
    }
    store.save_policy_decision(job_id, policy_decision)

    # 5. Save Evidence with signature
    evidence_payload = {
        "evidence_id": f"ev-{job_id}",
        "job_id": job_id,
        "commit_sha": commit_sha,
        "repository": repo,
        "verified": True,
        "finding_count": 1,
        "target_finding": {
            "rule_id": "python.lang.security.injection.sql-injection",
            "fingerprint": "fp-sqli-4455",
            "severity": "HIGH",
        },
        "verification_results": {
            "rescan_findings_count": 0,
            "target_vulnerability_eliminated": True,
            "verification_status": "passed",
            "test_summary": "Passed exploit proof and re-scan tests in gVisor.",
        },
        "patch_summary": {
            "title": "fix(security): parameterize SQL query execution",
            "files_changed": ["app/db.py"],
            "explanation": "Replaced string interpolation with parameterized DB cursor query.",
        },
    }
    signed_evidence = Ed25519EvidenceSigner().sign(evidence_payload)
    store.save_evidence(job_id, signed_evidence)

    # 6. Save PR
    pr_data = {
        "number": 42,
        "url": "https://github.com/patchproof-org/vulnerable-app/pull/42",
        "head_sha": commit_sha,
        "branch": "patchproof/fp-sqli-4455",
        "base_branch": "main",
        "repository": repo,
    }
    store.save_pr(job_id, pr_data)

    # 7. Query Job Detail and verify all GUI sections receive complete data
    res_detail = client.get(f"/jobs/{job_id}")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["state"] == "pr_created"
    assert detail["verified"] is True
    assert detail["pr"]["number"] == 42
    assert detail["pr"]["url"] == "https://github.com/patchproof-org/vulnerable-app/pull/42"
    assert len(detail["events"]) == 7

    # 8. Query Evidence endpoint
    res_ev = client.get(f"/jobs/{job_id}/evidence")
    assert res_ev.status_code == 200
    ev = res_ev.json()
    assert ev["verified"] is True
    assert ev["sha256_digest"] is not None
    assert ev["signature"] is not None

    # 9. Verify Signature endpoint
    res_verify = client.post("/evidence/verify", json=signed_evidence)
    assert res_verify.status_code == 200
    assert res_verify.json()["valid"] is True

    # 10. Query Repositories summary
    res_repos = client.get("/repositories")
    assert res_repos.status_code == 200
    repos = res_repos.json()["repositories"]
    assert len(repos) == 1
    assert repos[0]["repository"] == repo
    assert repos[0]["verified_prs"] == 1


def test_complete_e2e_failed_remediation_gui_flow(e2e_env):
    store = e2e_env["store"]
    client = e2e_env["client"]

    job_id = "job-e2e-fail-002"
    repo = "patchproof-org/broken-app"
    commit_sha = "f" * 40

    job = JobRecord(
        job_id=job_id,
        repository=repo,
        delivery_id="deliv-e2e-002",
        commit_sha=commit_sha,
        state=JobState.QUEUED,
    )
    store.create(job)

    # Transitions to failure during verification
    store.record_transition(job_id, "queued", "scanning", "Cloned source repository")
    store.record_transition(job_id, "scanning", "analyzing", "Analyzed findings")
    store.record_transition(job_id, "analyzing", "patching", "Applied candidate patch")
    store.record_transition(job_id, "patching", "verifying", "Verification tests started in gVisor")
    store.record_transition(
        job_id,
        "verifying",
        "failed",
        "Verification did not pass: pytest returned exit code 1. PR publication blocked.",
    )

    # Query Job Detail
    res_detail = client.get(f"/jobs/{job_id}")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["state"] == "failed"
    assert detail["verified"] is False
    assert detail["pr"] is None
    assert "pytest returned exit code 1" in detail["error"]
