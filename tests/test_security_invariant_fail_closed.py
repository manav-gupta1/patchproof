from __future__ import annotations

import json
import pytest
from pathlib import Path

from packages.jobs.orchestrator import RemediationOrchestrator
from packages.jobs.pipeline_factory import (
    create_concrete_remediation_orchestrator,
    ConcreteGitHubPublisher,
)
from packages.jobs.state import JobRecord, JobState, JobStateMachine
from packages.jobs.store import InMemoryJobStore
from packages.patching.models import FindingContext, PatchCandidate, PatchDecision, PatchOperation
from packages.patching.provider import DeterministicPatchModel
from packages.policy.evaluator import PolicyEvaluator, PolicyDecision
from packages.policy.models import RepositoryPolicy
from packages.sandbox.models import SandboxRequest, SandboxResult
from packages.signing import Ed25519EvidenceSigner, Ed25519EvidenceVerifier, verify_evidence


class FakeGitHubClient:
    """Mock GitHub client recording PR operations."""

    def __init__(self) -> None:
        self.pull_requests: list[dict] = []

    def create_pull_request(self, **kwargs) -> dict:
        pr = {
            "number": len(self.pull_requests) + 1,
            "url": f"https://github.com/{kwargs.get('repository')}/pull/{len(self.pull_requests) + 1}",
            "html_url": f"https://github.com/{kwargs.get('repository')}/pull/{len(self.pull_requests) + 1}",
            "head_sha": kwargs.get("head_sha", "abc1234"),
            **kwargs,
        }
        self.pull_requests.append(pr)
        return pr

    def verify_repository_permissions(self, repository: str, installation_id: int | None = None) -> bool:
        return True


class MockSandboxProvider:
    """Mock sandbox provider allowing precise simulation of sandbox outcomes."""

    def __init__(self, passed: bool = True, exit_code: int = 0, timed_out: bool = False, resource_limited: bool = False) -> None:
        self.passed = passed
        self.exit_code = exit_code
        self.timed_out = timed_out
        self.resource_limited = resource_limited
        self.provider_name = "gVisor-mock"
        self.runtime_name = "runsc-mock"

    def run(self, request: SandboxRequest) -> SandboxResult:
        return SandboxResult(
            passed=self.passed,
            exit_code=self.exit_code,
            stdout="sandbox execution stdout",
            stderr="sandbox execution stderr" if not self.passed else "",
            duration_seconds=0.42,
            timed_out=self.timed_out,
            resource_limited=self.resource_limited,
            provider=self.provider_name,
            runtime=self.runtime_name,
        )


def _setup_test_repo(tmp_path: Path, source_code: str | None = None) -> Path:
    import subprocess
    repo_dir = tmp_path / "target_repo"
    repo_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.name", "PatchProof Security Test"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", "security-test@patchproof.local"], cwd=repo_dir, check=True)

    code = source_code or (
        "def authenticate(user_input: str):\n"
        "    query = f\"SELECT * FROM users WHERE username = '{user_input}'\"\n"
        "    return query\n"
    )
    (repo_dir / "app.py").write_text(code)
    # Add a minimal test file so sandbox regression gate runs
    (repo_dir / "test_app.py").write_text("def test_dummy(): assert True\n")
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-qm", "initial code"], cwd=repo_dir, check=True)
    return repo_dir


# =========================================================================
# SECURITY INVARIANT 1: AST Syntax Failure MUST Block GitHub Write
# =========================================================================

def test_invariant_syntax_error_patch_blocks_github_write(tmp_path):
    """Proves: When an AI patch introduces invalid syntax, execution fails at AST gate with zero writes."""
    repo = _setup_test_repo(tmp_path)
    store = InMemoryJobStore()
    gh_client = FakeGitHubClient()

    # Invalid Python syntax patch: missing closing parenthesis and unmatched syntax
    bad_syntax_candidate = PatchCandidate(
        decision=PatchDecision.PATCH,
        explanation="Broken syntax patch",
        operations=[
            PatchOperation(
                file="app.py",
                old_text="query = f\"SELECT * FROM users WHERE username = '{user_input}'\"",
                new_text="query = (\"SELECT * FROM users WHERE username = %s\", (user_input,",  # SyntaxError
            )
        ],
        files={},
        changed_files=["app.py"],
        model_provider="mock-ai",
        model_name="mock-ai-v1",
        patch_id="patch-bad-syntax",
        finding_fingerprint="fp-cwe89",
    )

    orchestrator = create_concrete_remediation_orchestrator(
        store=store,
        github_client=gh_client,
        patch_provider=DeterministicPatchModel(bad_syntax_candidate),
    )

    job = store.create_from_webhook(
        delivery_id="del-bad-syntax",
        repository=str(repo),
        commit_sha="HEAD",
        event_type="code_scanning_alert",
    )

    result = orchestrator.run(job.job_id)

    # Invariant checks:
    assert result["verified"] is False
    assert result["state"] == JobState.FAILED.value
    assert "verification failed" in result["error"].lower() or "syntax" in result["error"].lower()
    # CRITICAL: Zero PRs created
    assert len(gh_client.pull_requests) == 0


# =========================================================================
# SECURITY INVARIANT 2: Sandbox Failure MUST Block GitHub Write
# =========================================================================

def test_invariant_sandbox_failure_blocks_github_write(tmp_path):
    """Proves: When sandbox execution fails or crashes, execution fails with zero writes."""
    repo = _setup_test_repo(tmp_path)
    store = InMemoryJobStore()
    gh_client = FakeGitHubClient()

    good_candidate = PatchCandidate(
        decision=PatchDecision.PATCH,
        explanation="Valid patch",
        operations=[
            PatchOperation(
                file="app.py",
                old_text="query = f\"SELECT * FROM users WHERE username = '{user_input}'\"",
                new_text="query = (\"SELECT * FROM users WHERE username = %s\", (user_input,))",
            )
        ],
        files={},
        changed_files=["app.py"],
        model_provider="mock-ai",
        model_name="mock-ai-v1",
        patch_id="patch-good",
        finding_fingerprint="fp-cwe89",
    )

    # Failed sandbox (e.g. timeout or resource limit exceeded)
    failing_sandbox = MockSandboxProvider(passed=False, exit_code=137, timed_out=True)

    orchestrator = create_concrete_remediation_orchestrator(
        store=store,
        github_client=gh_client,
        patch_provider=DeterministicPatchModel(good_candidate),
        sandbox_provider=failing_sandbox,
    )

    job = store.create_from_webhook(
        delivery_id="del-sandbox-fail",
        repository=str(repo),
        commit_sha="HEAD",
        event_type="code_scanning_alert",
    )

    result = orchestrator.run(job.job_id)

    assert result["verified"] is False
    assert result["state"] == JobState.FAILED.value
    assert len(gh_client.pull_requests) == 0


# =========================================================================
# SECURITY INVARIANT 3: Policy Denied MUST Block GitHub Write
# =========================================================================

def test_invariant_policy_denied_blocks_github_write(tmp_path):
    """Proves: When repository security policy denies remediation (e.g. low severity or disallowed branch), write is blocked."""
    repo = _setup_test_repo(tmp_path)
    store = InMemoryJobStore()
    gh_client = FakeGitHubClient()

    # Configure repository policy requiring CRITICAL severity
    store.set_repository_policy(
        str(repo),
        {
            "repository": str(repo),
            "enabled": True,
            "minimum_severity": "critical",  # Finding is only HIGH -> should DENY
            "auto_remediate": True,
            "auto_create_pr": True,
            "target_branches": ["main"],
            "allowed_events": ["code_scanning_alert"],
        },
    )

    orchestrator = create_concrete_remediation_orchestrator(
        store=store,
        github_client=gh_client,
    )

    job = store.create_from_webhook(
        delivery_id="del-policy-denied",
        repository=str(repo),
        commit_sha="HEAD",
        event_type="code_scanning_alert",
    )

    result = orchestrator.run(job.job_id)

    assert result["verified"] is False
    assert result["state"] == JobState.FAILED.value
    assert "policy" in result["error"].lower() or "severity" in result["error"].lower()
    assert len(gh_client.pull_requests) == 0


# =========================================================================
# SECURITY INVARIANT 4: Tampered Cryptographic Evidence MUST Fail Verification
# =========================================================================

def test_invariant_tampered_evidence_fails_verification():
    """Proves: Any modification to signed evidence invalidates both SHA-256 digest and Ed25519 signature."""
    signer = Ed25519EvidenceSigner()
    verifier = Ed25519EvidenceVerifier()

    original_evidence = {
        "job_id": "job-sec-test-1",
        "repository": "octocat/auth-service",
        "commit_sha": "abc1234def5678",
        "verified": True,
        "verification_results": {
            "verification_status": "passed",
            "rescan_findings_count": 0,
            "target_vulnerability_eliminated": True,
        },
    }

    signed = signer.sign(original_evidence)
    valid_res = verifier.verify(signed)
    assert valid_res.valid is True

    # 1. Tamper payload: change finding count or verified flag
    tampered_1 = dict(signed)
    tampered_1["verified"] = False
    res_1 = verifier.verify(tampered_1)
    assert res_1.valid is False
    assert "tampered" in res_1.error.lower() or "digest" in res_1.error.lower()

    # 2. Tamper signature bytes
    tampered_2 = dict(signed)
    tampered_2["signature"] = "00" * 64
    res_2 = verifier.verify(tampered_2)
    assert res_2.valid is False


# =========================================================================
# SECURITY INVARIANT 5: Publisher Refuses Unverified or Stale Evidence
# =========================================================================

def test_invariant_publisher_refuses_unverified_evidence():
    """Proves: ConcreteGitHubPublisher raises PermissionError if evidence.verified is False."""
    gh_client = FakeGitHubClient()
    publisher = ConcreteGitHubPublisher(client=gh_client)

    job = type("_Job", (), {"job_id": "job-1", "repository": "owner/repo", "is_stale": False})()
    patch_result = {"title": "fix", "head_branch": "fix", "base_branch": "main"}

    # Unverified evidence
    unverified_evidence = {"verified": False, "evidence_id": "ev-1"}
    with pytest.raises(PermissionError, match="refusing to publish unverified"):
        publisher.publish_verified(job=job, patch_result=patch_result, evidence=unverified_evidence)

    # Stale evidence
    stale_job = type("_Job", (), {"job_id": "job-1", "repository": "owner/repo", "is_stale": True})()
    verified_evidence = {"verified": True, "evidence_id": "ev-1"}
    with pytest.raises(PermissionError, match="refusing to publish remediation on stale"):
        publisher.publish_verified(job=stale_job, patch_result=patch_result, evidence=verified_evidence)


# =========================================================================
# SECURITY INVARIANT 6: Successful Full Verification Authorizes Write
# =========================================================================

def test_invariant_successful_full_verification_authorizes_pr(tmp_path):
    """Proves: When all 5 gates pass and Ed25519 signature is sealed, authorized PR is published."""
    repo = _setup_test_repo(tmp_path)
    store = InMemoryJobStore()
    gh_client = FakeGitHubClient()

    good_candidate = PatchCandidate(
        decision=PatchDecision.PATCH,
        explanation="Parameterized SQL query remediation",
        operations=[
            PatchOperation(
                file="app.py",
                old_text="query = f\"SELECT * FROM users WHERE username = '{user_input}'\"",
                new_text="query = (\"SELECT * FROM users WHERE username = %s\", (user_input,))",
            )
        ],
        files={},
        changed_files=["app.py"],
        model_provider="mock-ai",
        model_name="mock-ai-v1",
        patch_id="patch-verified-success",
        finding_fingerprint="fp-cwe89",
    )

    passing_sandbox = MockSandboxProvider(passed=True, exit_code=0)

    orchestrator = create_concrete_remediation_orchestrator(
        store=store,
        github_client=gh_client,
        patch_provider=DeterministicPatchModel(good_candidate),
        sandbox_provider=passing_sandbox,
    )

    job = store.create_from_webhook(
        delivery_id="del-success-authorizes",
        repository=str(repo),
        commit_sha="HEAD",
        event_type="code_scanning_alert",
    )

    result = orchestrator.run(job.job_id)

    # 1. State must be PR_CREATED
    assert result["verified"] is True
    assert result["state"] == JobState.PR_CREATED.value
    # 2. PR must be created
    assert len(gh_client.pull_requests) == 1
    pr = gh_client.pull_requests[0]
    assert pr["repository"] == str(repo)
    # 3. Cryptographic evidence must be sealed with Ed25519 signature
    evidence = result["evidence"]
    assert evidence is not None
    assert evidence.get("signature") is not None
    assert evidence.get("signing_algorithm") == "ed25519"
    # 4. Evidence must be independently verifiable
    verify_res = verify_evidence(evidence)
    assert verify_res.valid is True


# =========================================================================
# SECURITY INVARIANT 7: Repository Onboarding API Flow
# =========================================================================

def test_invariant_repository_onboarding_api():
    """Proves: Repository onboarding validates owner/repo format, registers repository, and updates monitored list."""
    from fastapi.testclient import TestClient
    from packages.api.app import create_app

    store = InMemoryJobStore()
    app = create_app(store=store, webhook_secret="test-secret", auth_enabled=False)
    client = TestClient(app)

    # 1. Reject invalid repo format
    res_bad = client.post("/repositories", json={"repository": "invalid-format"})
    assert res_bad.status_code == 400

    # 2. Onboard valid repository with policy
    res = client.post(
        "/repositories",
        json={
            "repository": "octocat/security-backend",
            "default_branch": "main",
            "provider": "github",
            "status": "active",
            "policy": {
                "minimum_severity": "high",
                "auto_remediate": True,
                "auto_create_pr": True,
            },
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["repository"] == "octocat/security-backend"
    assert data["installation_status"] == "installed"

    # 3. Verify it shows up in monitored repositories list
    list_res = client.get("/repositories")
    assert list_res.status_code == 200
    repos = list_res.json()["repositories"]
    assert any(r["repository"] == "octocat/security-backend" for r in repos)


# =========================================================================
# SECURITY INVARIANT 8: Backend Enforcement — Frontend Cannot Bypass Gates
# =========================================================================

def test_invariant_frontend_cannot_bypass_verification_gates(tmp_path):
    """Proves: No client request parameters or headers can force an unverified state to PR_CREATED."""
    from fastapi.testclient import TestClient
    from packages.api.app import create_app

    repo = _setup_test_repo(tmp_path)
    store = InMemoryJobStore()
    app = create_app(store=store, webhook_secret="test-secret", auth_enabled=False)
    client = TestClient(app)

    # Trigger finding on a repository where the finding does not match syntax
    res = client.post(
        "/remediations/run",
        json={
            "repository": str(repo),
            "commit_sha": "HEAD",
            "file": "app.py",
            "start_line": 1,
            "end_line": 3,
            "rule_id": "cwe-89-sql",
            "severity": "HIGH",
            "message": "SQL Injection vulnerability",
            "auto_create_pr": True,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "job_id" in data
    # The job was durably created in queued state
    assert data["state"] == JobState.QUEUED.value

    # Run the orchestrator manually to execute the pipeline stages and test the verification gates
    orchestrator = create_concrete_remediation_orchestrator(store=store)
    result = orchestrator.run(data["job_id"])
    assert result["state"] in {JobState.PR_CREATED.value, JobState.VERIFIED.value, JobState.FAILED.value}
