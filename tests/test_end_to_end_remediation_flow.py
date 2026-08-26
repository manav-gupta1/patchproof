import os
import subprocess
from pathlib import Path
import pytest

from packages.gitops.adapter import GitOpsAdapter
from packages.gitops.staging import (
    WorkspaceStaging,
    IsolatedWorkspace,
    DirtyRepositoryError,
)
from packages.jobs.orchestrator import RemediationOrchestrator
from packages.jobs.pipeline_factory import (
    create_concrete_remediation_orchestrator,
    ConcreteGitHubPublisher,
)
from packages.jobs.state import JobState, JobStateMachine, JobRecord
from packages.jobs.store import InMemoryJobStore
from packages.patching.apply import PatchApplier
from packages.patching.models import (
    FindingContext,
    PatchCandidate,
    PatchDecision,
)
from packages.patching.provider import (
    DeterministicPatchModel,
    RuleBasedPatchModel,
    get_patch_provider,
)
from packages.scanner.models import NormalizedFinding
from packages.scanner.service import ScannerService


def create_test_git_repo(path: Path, source_code: str | None = None) -> Path:
    """Helper to initialize a clean git repository for testing."""
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "PatchProof Test"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "test@patchproof.local"], cwd=path, check=True)
    
    code = source_code or (
        "import os\n\n"
        "def query_user(user_input: str):\n"
        "    # Potential vulnerability\n"
        "    query = f\"SELECT * FROM users WHERE username = '{user_input}'\"\n"
        "    return query\n"
    )
    (path / "app.py").write_text(code)
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(
        ["git", "-c", "user.name=PatchProof", "-c", "user.email=test@patchproof.local", "commit", "-qm", "initial commit"],
        cwd=path,
        check=True,
    )
    return path


def test_clean_repository_accepted(tmp_path):
    """Test that a clean git repository is accepted and staged."""
    source_repo = create_test_git_repo(tmp_path / "clean_repo")
    staging = WorkspaceStaging()
    
    workspace = staging.stage(source_repo)
    try:
        assert isinstance(workspace, IsolatedWorkspace)
        assert workspace.path.exists()
        assert (workspace.path / "app.py").exists()
        assert not workspace.is_dirty()
    finally:
        workspace.cleanup()


def test_dirty_repository_rejected(tmp_path):
    """Test that dirty repositories with uncommitted or untracked changes are rejected."""
    source_repo = create_test_git_repo(tmp_path / "dirty_repo")
    (source_repo / "uncommitted.txt").write_text("dirty content")

    staging = WorkspaceStaging()
    with pytest.raises(DirtyRepositoryError, match="uncommitted or untracked"):
        staging.stage(source_repo)


def test_isolated_staging_workspace_created_and_cleaned(tmp_path):
    """Test that an isolated temporary workspace is created and cleaned up."""
    source_repo = create_test_git_repo(tmp_path / "isolated_repo")
    staging = WorkspaceStaging()

    with staging.stage(source_repo) as ws:
        ws_path = ws.path
        assert ws_path.exists()
        assert ws_path != source_repo

    # After context exit, the isolated workspace must be cleaned up
    assert not ws_path.exists()


def test_patch_applied_only_to_staging_and_original_repository_remains_unchanged(tmp_path):
    """Test that patches are applied strictly to staging, leaving original repo untouched."""
    source_repo = create_test_git_repo(tmp_path / "untouched_repo")
    original_content = (source_repo / "app.py").read_text()
    original_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=source_repo, text=True
    ).strip()

    store = InMemoryJobStore()
    job = JobRecord(
        job_id="job-isolation-test-001",
        repository=str(source_repo),
        delivery_id="delivery-iso-001",
        commit_sha=original_sha,
    )
    store.create(job)

    orchestrator = create_concrete_remediation_orchestrator(store=store)
    result = orchestrator.run(job.job_id)

    assert result["state"] == JobState.PR_CREATED.value
    assert result["verified"] is True

    # Check original repository files and git commit
    assert (source_repo / "app.py").read_text() == original_content
    current_source_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=source_repo, text=True
    ).strip()
    assert current_source_sha == original_sha

    # Check that original git status is clean
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain=v1"], cwd=source_repo, text=True
    ).strip()
    assert not dirty


def test_verification_runs_after_patch(tmp_path):
    """Test that verification executes strictly after the patch is applied."""
    source_repo = create_test_git_repo(tmp_path / "order_repo")
    store = InMemoryJobStore()
    job = JobRecord(
        job_id="job-order-test-001",
        repository=str(source_repo),
        delivery_id="delivery-order-001",
        commit_sha="HEAD",
    )
    store.create(job)

    execution_order = []

    def mock_clone(repo, sha):
        execution_order.append("clone")
        return WorkspaceStaging().stage(repo, sha)

    def mock_scan(ws):
        execution_order.append("scan")
        return ScannerService().scan(ws)

    def mock_analyze(ws, findings):
        execution_order.append("analyze")
        return {"finding": findings[0], "context": FindingContext(
            fingerprint=findings[0].fingerprint,
            rule_id=findings[0].rule_id,
            path="app.py",
            start_line=4,
            end_line=4,
            severity="HIGH",
            source_excerpt="query = ...",
        ), "candidate": PatchCandidate(
            decision=PatchDecision.PATCH,
            explanation="fix",
            files={"app.py": "remediated code\n"},
            changed_files=["app.py"],
            patch_id="p-1",
        )}

    def mock_patch(ws, proposal):
        execution_order.append("patch")
        (Path(ws) / "app.py").write_text("remediated code\n")
        return {"head_branch": "patchproof/fix", "patch": "applied", "applied_files": ["app.py"]}

    def mock_verify(workspace, findings, proposal, patch_result):
        execution_order.append("verify")
        # Verify that during verification, the workspace contains the patched code
        assert (Path(workspace) / "app.py").read_text() == "remediated code\n"
        class _Outcome:
            verified = True
        return _Outcome()

    def mock_evidence(job, findings, proposal, patch_result, verification):
        execution_order.append("evidence")
        return {"verified": True, "evidence_id": "ev-001"}

    class MockPublisher:
        def publish_verified(self, **kwargs):
            execution_order.append("publish")
            return {"url": "https://github.com/example/repo/pull/1", "number": 1}

    orchestrator = RemediationOrchestrator(
        store=store,
        state_machine=JobStateMachine(),
        clone=mock_clone,
        scan=mock_scan,
        analyze=mock_analyze,
        patch=mock_patch,
        verify=mock_verify,
        evidence=mock_evidence,
        github=MockPublisher(),
    )

    result = orchestrator.run(job.job_id)
    assert result["state"] == JobState.PR_CREATED.value
    assert execution_order == ["clone", "scan", "analyze", "patch", "verify", "evidence", "publish"]


def test_failed_verification_causes_remediation_failure(tmp_path):
    """Test that if verification fails, remediation fails and no PR is published."""
    source_repo = create_test_git_repo(tmp_path / "failed_verify_repo")
    store = InMemoryJobStore()
    job = JobRecord(
        job_id="job-verify-fail-001",
        repository=str(source_repo),
        delivery_id="delivery-vfail-001",
        commit_sha="HEAD",
    )
    store.create(job)

    published_called = False

    class FailingPublisher:
        def publish_verified(self, **kwargs):
            nonlocal published_called
            published_called = True
            return {"url": "should-not-reach"}

    orchestrator = create_concrete_remediation_orchestrator(
        store=store,
        github_client=FailingPublisher(),
    )
    # Inject a verifier that fails
    class FailedVerification:
        verified = False
    orchestrator.verify = lambda **kwargs: FailedVerification()

    result = orchestrator.run(job.job_id)

    assert result["state"] == JobState.FAILED.value
    assert result["verified"] is False
    assert result["error"] == "verification failed"
    assert not published_called

    # Durable state in store must be FAILED
    final_job = store.get(job.job_id)
    assert final_job.state == JobState.FAILED


def test_successful_verification_produces_successful_remediation_result(tmp_path):
    """Test that successful verification produces structured result with PR and signed evidence."""
    from packages.signing import verify_evidence

    source_repo = create_test_git_repo(tmp_path / "success_repo")
    store = InMemoryJobStore()
    job = JobRecord(
        job_id="job-success-001",
        repository=str(source_repo),
        delivery_id="delivery-succ-001",
        commit_sha="HEAD",
    )
    store.create(job)

    orchestrator = create_concrete_remediation_orchestrator(store=store)
    result = orchestrator.run(job.job_id)

    assert result["state"] == JobState.PR_CREATED.value
    assert result["verified"] is True
    assert result["job_id"] == "job-success-001"
    assert "pr" in result
    assert result["pr"]["url"]
    assert "evidence" in result

    evidence = result["evidence"]
    assert evidence["sha256_digest"] is not None
    assert evidence["signature"] is not None
    assert evidence["signing_algorithm"] == "ed25519"
    assert evidence["signing_key_id"] is not None

    verification_res = verify_evidence(evidence)
    assert verification_res.valid is True
    assert verification_res.error is None

    final_job = store.get(job.job_id)
    assert final_job.state == JobState.PR_CREATED


def test_remediation_job_failure_represented_correctly(tmp_path):
    """Test that unhandled errors during pipeline execution transition job to FAILED."""
    source_repo = create_test_git_repo(tmp_path / "error_repo")
    store = InMemoryJobStore()
    job = JobRecord(
        job_id="job-error-001",
        repository=str(source_repo),
        delivery_id="delivery-err-001",
        commit_sha="HEAD",
    )
    store.create(job)

    orchestrator = create_concrete_remediation_orchestrator(store=store)
    # Inject an exception during scan
    orchestrator.scan = lambda ws: (_ for _ in ()).throw(RuntimeError("AST syntax error"))

    result = orchestrator.run(job.job_id)

    assert result["state"] == JobState.FAILED.value
    assert result["verified"] is False
    assert "AST syntax error" in result["error"]

    final_job = store.get(job.job_id)
    assert final_job.state == JobState.FAILED


def test_secrets_not_leaked_in_results(tmp_path, monkeypatch):
    """Test that configured secrets are not exposed in returned remediation results."""
    secret_key = "sk-super-secret-key-12345"
    monkeypatch.setenv("OPENAI_API_KEY", secret_key)
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "webhook-secret-999")

    source_repo = create_test_git_repo(tmp_path / "secret_repo")
    store = InMemoryJobStore()
    job = JobRecord(
        job_id="job-secret-001",
        repository=str(source_repo),
        delivery_id="delivery-sec-001",
        commit_sha="HEAD",
    )
    store.create(job)

    orchestrator = create_concrete_remediation_orchestrator(store=store)
    result = orchestrator.run(job.job_id)

    result_str = str(result)
    assert secret_key not in result_str
    assert "webhook-secret-999" not in result_str
