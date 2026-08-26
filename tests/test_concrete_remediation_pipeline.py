import os
import subprocess
from pathlib import Path
import pytest

from packages.gitops.adapter import GitOpsAdapter, GitOpsError
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
from packages.patching.validator import PatchValidator
from packages.scanner.models import NormalizedFinding
from packages.scanner.service import ScannerService


def init_git_repo(path: Path) -> Path:
    """Helper to initialize a clean git repository."""
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "PatchProof Test"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "test@patchproof.local"], cwd=path, check=True)
    (path / "app.py").write_text(
        "import os\n\n"
        "def query_user(user_input: str):\n"
        "    query = f\"SELECT * FROM users WHERE username = '{user_input}'\"\n"
        "    return query\n"
    )
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(
        ["git", "-c", "user.name=PatchProof", "-c", "user.email=test@patchproof.local", "commit", "-qm", "baseline"],
        cwd=path,
        check=True,
    )
    return path


def test_workspace_staging_clean_repo(tmp_path):
    source = init_git_repo(tmp_path / "source_repo")
    staging = WorkspaceStaging()
    workspace = staging.stage(source)

    assert isinstance(workspace, IsolatedWorkspace)
    assert workspace.path.exists()
    assert workspace.path != source
    assert (workspace.path / "app.py").exists()
    assert not workspace.is_dirty()

    # Verify isolated changes do not affect source
    (workspace.path / "app.py").write_text("modified in workspace")
    assert "modified in workspace" not in (source / "app.py").read_text()

    # Cleanup
    workspace.cleanup()
    assert not workspace.path.exists()


def test_workspace_staging_dirty_repo_rejected(tmp_path):
    source = init_git_repo(tmp_path / "dirty_repo")
    (source / "untracked.py").write_text("# untracked file")

    staging = WorkspaceStaging()
    with pytest.raises(DirtyRepositoryError):
        staging.stage(source)


def test_isolated_workspace_context_manager(tmp_path):
    source = init_git_repo(tmp_path / "ctx_repo")
    staging = WorkspaceStaging()
    
    with staging.stage(source) as ws:
        ws_path = ws.path
        assert ws_path.exists()

    assert not ws_path.exists()


def test_scanner_service_structured_findings(tmp_path):
    repo = init_git_repo(tmp_path / "scan_repo")
    scanner = ScannerService()
    findings = scanner.scan(repo)

    assert len(findings) >= 1
    finding = findings[0]
    assert isinstance(finding, NormalizedFinding)
    assert finding.rule_id == "python.sql-injection"
    assert finding.severity in {"HIGH", "CRITICAL", "MEDIUM", "LOW", "INFO"}
    assert finding.location.file == "app.py"
    assert finding.location.start_line >= 1
    assert finding.fingerprint


@pytest.mark.asyncio
async def test_rule_based_patch_model():
    model = RuleBasedPatchModel()
    context = FindingContext(
        fingerprint="python.sql-injection:app.py:4",
        rule_id="python.sql-injection",
        path="app.py",
        start_line=4,
        end_line=4,
        severity="HIGH",
        source_excerpt="query = f\"SELECT * FROM users WHERE username = '{user_input}'\"",
    )

    candidate = await model.propose(context)
    assert candidate.decision == PatchDecision.PATCH
    assert "app.py" in candidate.files
    assert "%s" in candidate.files["app.py"] or "sanitize" in candidate.files["app.py"]
    assert candidate.patch_id


def test_patch_provider_factory():
    provider = get_patch_provider()
    assert isinstance(provider, RuleBasedPatchModel)

    custom_candidate = PatchCandidate(
        decision=PatchDecision.PATCH,
        explanation="custom",
        files={"app.py": "content"},
        changed_files=["app.py"],
        patch_id="patch-123",
    )
    det_provider = get_patch_provider(candidate=custom_candidate)
    assert isinstance(det_provider, DeterministicPatchModel)


def test_patch_validation_and_application(tmp_path):
    repo = init_git_repo(tmp_path / "apply_repo")
    applier = PatchApplier()
    candidate = PatchCandidate(
        decision=PatchDecision.PATCH,
        explanation="Fix sql injection",
        files={"app.py": "def query_user(user_input: str):\n    return ('SELECT * FROM users WHERE username = %s', (user_input,))\n"},
        changed_files=["app.py"],
        patch_id="patch-sql-1",
    )

    applied = applier.apply(repo, candidate)
    assert "app.py" in applied
    assert "%s" in (repo / "app.py").read_text()


def test_unverified_github_publication_rejected():
    publisher = ConcreteGitHubPublisher()
    job = type("Job", (), {"repository": "example/repo", "commit_sha": "abc1234", "job_id": "job-1"})()
    
    with pytest.raises(PermissionError, match="unverified"):
        publisher.publish_verified(
            job=job,
            patch_result={"head_branch": "patchproof/fix"},
            evidence={"verified": False},
        )


def test_successful_end_to_end_concrete_remediation(tmp_path):
    source = init_git_repo(tmp_path / "e2e_repo")
    store = InMemoryJobStore()
    job = JobRecord(
        job_id="job-e2e-001",
        repository=str(source),
        delivery_id="delivery-e2e-001",
        commit_sha="HEAD",
    )
    store.create(job)

    orchestrator = create_concrete_remediation_orchestrator(store=store)
    result = orchestrator.run(job.job_id)

    assert result["state"] == JobState.PR_CREATED.value
    assert "pr" in result
    assert result["pr"]["url"]

    # Verify final job state in store
    final_job = store.get(job.job_id)
    assert final_job.state == JobState.PR_CREATED


def test_failed_remediation_when_no_findings(tmp_path):
    empty_repo = tmp_path / "empty_repo"
    empty_repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=empty_repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=empty_repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.local"], cwd=empty_repo, check=True)
    (empty_repo / "clean.py").write_text("# clean file\n")
    subprocess.run(["git", "add", "."], cwd=empty_repo, check=True)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "clean"], cwd=empty_repo, check=True)

    store = InMemoryJobStore()
    job = JobRecord(
        job_id="job-fail-001",
        repository=str(empty_repo),
        delivery_id="delivery-fail-001",
        commit_sha="HEAD",
    )
    store.create(job)

    # Use an orchestrator where scanner returns empty findings
    orchestrator = create_concrete_remediation_orchestrator(store=store)
    orchestrator.scan = lambda ws: []

    result = orchestrator.run(job.job_id)
    assert result["state"] == JobState.FAILED.value
    assert "error" in result

    final_job = store.get(job.job_id)
    assert final_job.state == JobState.FAILED
