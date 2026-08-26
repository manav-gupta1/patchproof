from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any
import pytest

from packages.github.check_runs import (
    CheckRunRef,
    GitHubCheckRunReporter,
    NullCheckRunReporter,
)
from packages.github.client import GitHubAppClient
from packages.github.transport import GitHubAPIError
from packages.jobs.orchestrator import RemediationOrchestrator
from packages.jobs.pipeline_factory import create_concrete_remediation_orchestrator
from packages.jobs.state import JobRecord, JobState, JobStateMachine
from packages.jobs.store import InMemoryJobStore
from packages.store.postgres import PostgresJobStore
from packages.webhooks.handlers import WebhookDispatcher


class MockGitHubCheckRunTransport:
    def __init__(self):
        self.check_runs: dict[int, dict[str, Any]] = {}
        self.next_id = 1000
        self.calls: list[dict[str, Any]] = []

    def create_check_run(
        self,
        *,
        token: str,
        owner: str,
        repo: str,
        name: str,
        head_sha: str,
        status: str = "queued",
        conclusion: str | None = None,
        completed_at: str | None = None,
        external_id: str | None = None,
        output: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        cr_id = self.next_id
        self.next_id += 1
        record = {
            "id": cr_id,
            "name": name,
            "head_sha": head_sha,
            "status": status,
            "conclusion": conclusion,
            "completed_at": completed_at,
            "external_id": external_id,
            "output": output or {},
            "owner": owner,
            "repo": repo,
            "html_url": f"https://github.com/{owner}/{repo}/runs/{cr_id}",
        }
        self.check_runs[cr_id] = record
        self.calls.append({"action": "create", "id": cr_id, "record": record, "token": token})
        return record

    def update_check_run(
        self,
        *,
        token: str,
        owner: str,
        repo: str,
        check_run_id: int,
        status: str | None = None,
        conclusion: str | None = None,
        completed_at: str | None = None,
        output: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if check_run_id not in self.check_runs:
            raise GitHubAPIError(f"Check Run {check_run_id} not found")
        record = self.check_runs[check_run_id]
        if status is not None:
            record["status"] = status
        if conclusion is not None:
            record["conclusion"] = conclusion
        if completed_at is not None:
            record["completed_at"] = completed_at
        if output is not None:
            record["output"] = output
        self.calls.append({"action": "update", "id": check_run_id, "record": record, "token": token})
        return record


class MockAuth:
    def __init__(self, token: str = "ghs_testsecrettoken123456"):
        self.token = token

    def installation_token(self, inst_id: int):
        from packages.github.auth import InstallationToken
        return InstallationToken(token=self.token, expires_at=int(1e9))


def test_check_run_reporter_lifecycle():
    """Test full Check Run lifecycle: queued -> in_progress -> completed (success)."""
    transport = MockGitHubCheckRunTransport()
    auth = MockAuth()
    client = GitHubAppClient(auth=auth, transport=transport)
    reporter = GitHubCheckRunReporter(client=client)

    job = JobRecord(
        job_id="job-cr-test-1",
        repository="octocat/hello-world",
        commit_sha="a" * 40,
        installation_id=123,
    )

    # 1. Queued
    queued_ref = reporter.report_queued(job)
    assert queued_ref is not None
    assert queued_ref.status == "queued"
    assert queued_ref.id == 1000
    job.check_run_id = queued_ref.id

    # 2. In Progress
    in_prog_ref = reporter.report_in_progress(job, check_run_id=job.check_run_id)
    assert in_prog_ref is not None
    assert in_prog_ref.status == "in_progress"
    assert in_prog_ref.id == 1000

    # 3. Completed Success
    evidence = {
        "target_finding": {"rule_id": "python.sql-injection", "severity": "HIGH"},
        "verification_results": {"test_summary": "AST valid; 0 residual findings."},
        "sha256_digest": "abcdef1234567890",
        "signing_key_id": "patchproof-key-1",
        "signing_algorithm": "ed25519",
    }
    pr = {"number": 42, "url": "https://github.com/octocat/hello-world/pull/42"}

    success_ref = reporter.report_success(
        job,
        check_run_id=job.check_run_id,
        pr=pr,
        evidence=evidence,
    )
    assert success_ref is not None
    assert success_ref.status == "completed"
    assert success_ref.conclusion == "success"

    # Verify check run record details in transport
    final_record = transport.check_runs[1000]
    assert final_record["status"] == "completed"
    assert final_record["conclusion"] == "success"
    assert "Verification Passed" in final_record["output"]["text"]
    assert "python.sql-injection" in final_record["output"]["text"]
    assert "#42" in final_record["output"]["text"]
    assert "abcdef1234567890" in final_record["output"]["text"]


def test_check_run_reporter_failure():
    """Test Check Run reporting for a failure scenario."""
    transport = MockGitHubCheckRunTransport()
    auth = MockAuth()
    client = GitHubAppClient(auth=auth, transport=transport)
    reporter = GitHubCheckRunReporter(client=client)

    job = JobRecord(
        job_id="job-cr-fail-1",
        repository="octocat/hello-world",
        commit_sha="b" * 40,
        installation_id=123,
    )

    queued_ref = reporter.report_queued(job)
    assert queued_ref is not None
    job.check_run_id = queued_ref.id

    fail_ref = reporter.report_failure(
        job,
        check_run_id=job.check_run_id,
        stage="verification_gate",
        error="SyntaxError: invalid syntax on line 12",
    )
    assert fail_ref is not None
    assert fail_ref.status == "completed"
    assert fail_ref.conclusion == "failure"

    record = transport.check_runs[queued_ref.id]
    assert record["conclusion"] == "failure"
    assert "verification_gate" in record["output"]["text"]
    assert "SyntaxError" in record["output"]["text"]


def test_check_run_reporter_secret_sanitization():
    """Test that secret tokens and private keys never leak in Check Run output."""
    transport = MockGitHubCheckRunTransport()
    secret_token = "ghs_supersecretinstallationtoken999"
    auth = MockAuth(token=secret_token)
    client = GitHubAppClient(auth=auth, transport=transport)
    reporter = GitHubCheckRunReporter(client=client)

    job = JobRecord(
        job_id="job-cr-secret-test",
        repository="octocat/hello-world",
        commit_sha="c" * 40,
        installation_id=123,
    )

    # Attempt reporting failure with secret token embedded in error message
    leak_error = f"Authentication to https://x-access-token:{secret_token}@github.com failed"
    reporter.report_failure(job, stage="checkout", error=leak_error)

    # Check the created record
    created = transport.calls[-1]["record"]
    assert secret_token not in created["output"]["summary"]
    assert secret_token not in created["output"]["text"]
    assert "REDACTED" in created["output"]["text"] or "REDACTED" in created["output"]["summary"]


def test_webhook_dispatcher_triggers_check_run_queued():
    """Test that WebhookDispatcher creates a queued Check Run and persists check_run_id."""
    transport = MockGitHubCheckRunTransport()
    auth = MockAuth()
    client = GitHubAppClient(auth=auth, transport=transport)
    reporter = GitHubCheckRunReporter(client=client)

    store = InMemoryJobStore()
    dispatcher = WebhookDispatcher(jobs=store, enqueue=lambda j: None, check_runs=reporter)

    class MockEvent:
        event = "pull_request"
        delivery_id = "deliv-webhook-cr-001"
        payload = {
            "repository": {"full_name": "acme/check-run-repo"},
            "pull_request": {"head": {"sha": "d" * 40}},
            "installation": {"id": 888},
        }

    res = dispatcher.dispatch(MockEvent())
    assert res["accepted"] is True

    job = store.get(res["job_id"])
    assert job is not None
    assert job.check_run_id == 1000
    assert transport.check_runs[1000]["status"] == "queued"
    assert transport.check_runs[1000]["owner"] == "acme"
    assert transport.check_runs[1000]["repo"] == "check-run-repo"


def test_end_to_end_orchestrator_check_run_success(tmp_path):
    """Test that concrete orchestrator drives Check Run to completed success."""
    source_repo = tmp_path / "cr_success_repo"
    source_repo.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=source_repo, check=True)
    (source_repo / "app.py").write_text(
        "def query_user(user_input: str):\n"
        "    query = f\"SELECT * FROM users WHERE username = '{user_input}'\"\n"
        "    return query\n"
    )
    subprocess.run(["git", "add", "."], cwd=source_repo, check=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@test.local", "commit", "-qm", "initial"],
        cwd=source_repo,
        check=True,
    )
    head_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source_repo, text=True).strip()

    transport = MockGitHubCheckRunTransport()
    auth = MockAuth()
    client = GitHubAppClient(auth=auth, transport=transport)
    reporter = GitHubCheckRunReporter(client=client)

    class MockPublisherClient:
        def create_pull_request(self, **kwargs):
            return {"number": 10, "url": "https://github.com/example/repo/pull/10", "head_sha": head_sha}

    store = InMemoryJobStore()
    job = JobRecord(
        job_id="job-e2e-cr-success",
        repository=str(source_repo),
        delivery_id="deliv-e2e-cr-1",
        commit_sha=head_sha,
        installation_id=42,
    )
    store.create(job)

    orchestrator = create_concrete_remediation_orchestrator(
        store=store,
        github_client=MockPublisherClient(),
        check_run_reporter=reporter,
    )

    result = orchestrator.run(job.job_id)

    assert result["state"] == JobState.PR_CREATED.value
    assert result["verified"] is True

    # Ensure Check Run lifecycle reached completed / success
    assert len(transport.calls) >= 2  # in_progress and completed
    last_call = transport.calls[-1]
    assert last_call["record"]["status"] == "completed"
    assert last_call["record"]["conclusion"] == "success"
    assert "Verification Passed" in last_call["record"]["output"]["text"]


def test_end_to_end_orchestrator_check_run_verification_failure(tmp_path):
    """Test that verification failure drives Check Run to completed failure."""
    source_repo = tmp_path / "cr_fail_repo"
    source_repo.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=source_repo, check=True)
    (source_repo / "app.py").write_text(
        "def query_user(user_input: str):\n"
        "    query = f\"SELECT * FROM users WHERE username = '{user_input}'\"\n"
        "    return query\n"
    )
    subprocess.run(["git", "add", "."], cwd=source_repo, check=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@test.local", "commit", "-qm", "initial"],
        cwd=source_repo,
        check=True,
    )
    head_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source_repo, text=True).strip()

    transport = MockGitHubCheckRunTransport()
    auth = MockAuth()
    client = GitHubAppClient(auth=auth, transport=transport)
    reporter = GitHubCheckRunReporter(client=client)

    store = InMemoryJobStore()
    job = JobRecord(
        job_id="job-e2e-cr-verif-fail",
        repository=str(source_repo),
        delivery_id="deliv-e2e-cr-2",
        commit_sha=head_sha,
    )
    store.create(job)

    class FailingVerification:
        verified = False
        rescan_count = 1
        test_summary = "Residual SQL injection detected after patch application."

    orchestrator = create_concrete_remediation_orchestrator(
        store=store,
        check_run_reporter=reporter,
    )
    # Monkeypatch verify stage to simulate verification rejection
    orchestrator.verify = lambda **kw: FailingVerification()

    result = orchestrator.run(job.job_id)

    assert result["state"] == JobState.FAILED.value
    assert result["verified"] is False

    last_call = transport.calls[-1]
    assert last_call["record"]["status"] == "completed"
    assert last_call["record"]["conclusion"] == "failure"
    assert "verification_gate" in last_call["record"]["output"]["text"]


def test_check_run_reporter_api_failure_does_not_break_remediation(tmp_path):
    """Test that GitHub Check Run API failures do NOT crash the remediation pipeline."""
    source_repo = tmp_path / "cr_api_fail_repo"
    source_repo.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=source_repo, check=True)
    (source_repo / "app.py").write_text(
        "def query_user(user_input: str):\n"
        "    query = f\"SELECT * FROM users WHERE username = '{user_input}'\"\n"
        "    return query\n"
    )
    subprocess.run(["git", "add", "."], cwd=source_repo, check=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@test.local", "commit", "-qm", "initial"],
        cwd=source_repo,
        check=True,
    )
    head_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source_repo, text=True).strip()

    class ExplodingCheckRunReporter(GitHubCheckRunReporter):
        def __init__(self):
            pass
        def report_queued(self, job):
            raise GitHubAPIError("GitHub API 503 Service Unavailable")
        def report_in_progress(self, job, check_run_id=None):
            raise GitHubAPIError("GitHub API 503 Service Unavailable")
        def report_success(self, job, **kw):
            raise GitHubAPIError("GitHub API 503 Service Unavailable")
        def report_failure(self, job, **kw):
            raise GitHubAPIError("GitHub API 503 Service Unavailable")

    store = InMemoryJobStore()
    job = JobRecord(
        job_id="job-e2e-cr-api-fail",
        repository=str(source_repo),
        delivery_id="deliv-e2e-cr-3",
        commit_sha=head_sha,
    )
    store.create(job)

    class MockPublisherClient:
        def create_pull_request(self, **kwargs):
            return {"number": 11, "url": "https://github.com/example/repo/pull/11", "head_sha": head_sha}

    orchestrator = create_concrete_remediation_orchestrator(
        store=store,
        github_client=MockPublisherClient(),
        check_run_reporter=ExplodingCheckRunReporter(),
    )

    # Remediation pipeline should succeed despite Check Run reporting failures
    result = orchestrator.run(job.job_id)
    assert result["state"] == JobState.PR_CREATED.value
    assert result["verified"] is True
    assert result["pr"]["number"] == 11


def test_postgres_store_persists_check_run_id():
    """Test that PostgresJobStore saves and retrieves check_run_id correctly."""
    store = PostgresJobStore("sqlite:///:memory:")
    store.create_schema()

    job = store.create_from_webhook(
        delivery_id="deliv-pg-cr-001",
        repository="acme/pg-cr-repo",
        commit_sha="e" * 40,
        event_type="pull_request",
        installation_id=123,
        check_run_id=987654321,
    )

    assert job.check_run_id == 987654321

    retrieved = store.get(job.job_id)
    assert retrieved is not None
    assert retrieved.check_run_id == 987654321

    # Test update
    store.save_check_run_id(job.job_id, 123456789)
    updated = store.get(job.job_id)
    assert updated.check_run_id == 123456789
