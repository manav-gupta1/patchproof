import subprocess
from pathlib import Path
import pytest

from packages.sandbox.policy import SandboxPolicy, SandboxPolicyError
from packages.sandbox.runner import DockerSandboxRunner, SandboxResult
from packages.sandbox.gvisor import GVisorSandboxRunner
from packages.jobs.pipeline_factory import create_concrete_remediation_orchestrator
from packages.jobs.state import JobRecord, JobState
from packages.jobs.store import InMemoryJobStore
from packages.patching.models import PatchCandidate, PatchDecision


def test_sandbox_policy_validation():
    """Test policy boundary enforcement."""
    valid_policy = SandboxPolicy(timeout_seconds=60, memory_mb=512, pids_limit=128)
    valid_policy.validate()
    assert valid_policy.network_enabled is False
    assert valid_policy.readonly_root is True

    with pytest.raises(SandboxPolicyError, match="network access is disabled"):
        SandboxPolicy(network_enabled=True).validate()

    with pytest.raises(SandboxPolicyError, match="timeout must be between"):
        SandboxPolicy(timeout_seconds=0).validate()


def test_docker_sandbox_runner_command_hardening(tmp_path):
    """Test that DockerSandboxRunner builds hardened container arguments."""
    policy = SandboxPolicy(timeout_seconds=120, memory_mb=256, pids_limit=64)
    runner = DockerSandboxRunner(
        image="patchproof/runner:latest",
        timeout=120,
        policy=policy,
        container_cli="docker",
    )
    cmd = runner._build_docker_command(tmp_path, ["python", "-m", "pytest", "-q"])

    assert cmd[0] == "docker"
    assert cmd[1] == "run"
    assert "--rm" in cmd
    assert "--network=none" in cmd
    assert "--cap-drop=ALL" in cmd
    assert "--security-opt=no-new-privileges" in cmd
    assert "--pids-limit=64" in cmd
    assert "--memory=256m" in cmd
    assert f"-v" in cmd
    assert f"{tmp_path}:/workspace:rw" in cmd
    assert "-w" in cmd
    assert "/workspace" in cmd
    assert "patchproof/runner:latest" in cmd
    assert cmd[-4:] == ["python", "-m", "pytest", "-q"]


def test_gvisor_sandbox_runner_injects_runsc_runtime(tmp_path):
    """Test that GVisorSandboxRunner sets the runsc runtime."""
    runner = GVisorSandboxRunner(
        image="python:3.12-slim",
        runtime="runsc",
    )
    cmd = runner._build_docker_command(tmp_path, ["pytest"])

    assert "--runtime" in cmd
    idx = cmd.index("--runtime")
    assert cmd[idx + 1] == "runsc"
    assert "--network=none" in cmd
    assert "--cap-drop=ALL" in cmd


def test_docker_sandbox_runner_secret_sanitization(tmp_path, monkeypatch):
    """Test that secrets in output from sandbox executions are sanitized."""
    secret_token = "ghs_sandbox_secret_token_1234567890"

    def fake_subprocess_run(cmd, **kwargs):
        class Result:
            returncode = 1
            stdout = f"Executed with token {secret_token}"
            stderr = f"Error with Bearer eyJhbGciOiJSUzI1NiJ9.test.sig"
        return Result()

    monkeypatch.setattr(subprocess, "run", fake_subprocess_run)

    runner = DockerSandboxRunner(image="python:3.12-slim")
    result = runner.run(tmp_path, ["test"])

    assert secret_token not in result.stdout
    assert "[REDACTED_TOKEN]" in result.stdout
    assert "Bearer [REDACTED_JWT]" in result.stderr


def test_syntax_error_in_patch_fails_verification_gate(tmp_path):
    """Test that a patch introducing a Python syntax error is rejected at verification."""
    source_repo = tmp_path / "syntax_repo"
    source_repo.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=source_repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test Bot"], cwd=source_repo, check=True)
    subprocess.run(["git", "config", "user.email", "bot@test.local"], cwd=source_repo, check=True)
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

    # Create a patch provider that produces invalid Python syntax (e.g. unclosed parenthesis)
    broken_candidate = PatchCandidate(
        decision=PatchDecision.PATCH,
        explanation="Broken syntax fix",
        files={"app.py": "def query_user(user_input: str\n    return query\n"},
        changed_files=["app.py"],
        model_provider="mock",
        model_name="broken",
        patch_id="p-broken",
        finding_fingerprint="fp-1",
        title="fix(security): broken syntax",
    )

    class BrokenPatchProvider:
        async def propose(self, context):
            return broken_candidate

    store = InMemoryJobStore()
    job = JobRecord(
        job_id="job-syntax-fail-001",
        repository=str(source_repo),
        delivery_id="delivery-syntax-001",
        commit_sha=head_sha,
    )
    store.create(job)

    orchestrator = create_concrete_remediation_orchestrator(
        store=store,
        patch_provider=BrokenPatchProvider(),
    )

    result = orchestrator.run(job.job_id)

    assert result["state"] == JobState.FAILED.value
    assert result["verified"] is False
    assert result["error"] == "verification failed"
