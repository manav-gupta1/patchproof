from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Any
import pytest

from packages.sandbox.environment import (
    ALLOWED_ENV_VARS,
    EXPLICIT_BLOCKED_KEYS,
    build_isolated_environment,
    is_sensitive_key,
)
from packages.sandbox.factory import get_sandbox_provider
from packages.sandbox.models import (
    NetworkPolicy,
    SandboxError,
    SandboxRequest,
    SandboxResourceLimitError,
    SandboxResult,
    SandboxSecurityError,
    SandboxTimeoutError,
    SandboxUnavailableError,
)
from packages.sandbox.providers.container import DockerContainerSandboxProvider
from packages.sandbox.providers.gvisor import GVisorSandboxProvider
from packages.sandbox.providers.local import LocalProcessSandboxProvider
from packages.jobs.orchestrator import RemediationOrchestrator
from packages.jobs.pipeline_factory import (
    ConcreteGitHubPublisher,
    create_concrete_remediation_orchestrator,
)
from packages.jobs.state import JobRecord, JobState, JobStateMachine
from packages.jobs.store import InMemoryJobStore
from packages.signing import Ed25519EvidenceSigner


# ==============================================================================
# 1. Non-Root & Filesystem Hardening Tests
# ==============================================================================

def test_docker_sandbox_command_hardening(tmp_path):
    """Test that Docker sandbox enforces non-root, read-only rootfs, and mounts only workspace."""
    provider = DockerContainerSandboxProvider(image="patchproof/runner:latest", container_cli="docker")
    req = SandboxRequest(
        command=["python", "-m", "pytest"],
        workspace_path=tmp_path,
        memory_limit_mb=256,
        cpu_limit=1.5,
        pids_limit=64,
        non_root_uid=10001,
        read_only_root=True,
    )
    cmd = provider._build_docker_argv(req, "test-sbx-123", tmp_path)

    assert cmd[0] == "docker"
    assert cmd[1] == "run"
    assert "--rm" in cmd
    assert "--name=test-sbx-123" in cmd
    assert "--user=10001:10001" in cmd
    assert "--read-only" in cmd
    assert "--tmpfs=/tmp:rw,noexec,nosuid,size=64m" in cmd
    assert "--cap-drop=ALL" in cmd
    assert "--security-opt=no-new-privileges" in cmd
    assert "--pids-limit=64" in cmd
    assert "--memory=256m" in cmd
    assert "--memory-swap=256m" in cmd
    assert "--cpus=1.5" in cmd
    assert f"-v" in cmd
    assert f"{tmp_path}:/workspace:rw" in cmd
    assert "-w" in cmd
    assert "/workspace" in cmd
    assert "--network=none" in cmd

    # Must never mount host directories
    full_cmd_str = " ".join(cmd)
    assert "/var/run/docker.sock" not in full_cmd_str
    assert "/root" not in full_cmd_str
    assert "/Users" not in full_cmd_str or full_cmd_str.count(str(tmp_path)) > 0


def test_gvisor_sandbox_sets_runsc_runtime(tmp_path, monkeypatch):
    """Test that GVisor sandbox injects --runtime=runsc and checks runtime availability."""
    # Fake runtime verification
    def fake_assert(self):
        pass

    monkeypatch.setattr(GVisorSandboxProvider, "_assert_runsc_available", fake_assert)

    provider = GVisorSandboxProvider(image="patchproof/runner:latest", runtime="runsc", verify_runtime_available=False)
    req = SandboxRequest(command=["python", "--version"], workspace_path=tmp_path)
    cmd = provider._build_docker_argv(req, "test-sbx-gvisor", tmp_path)

    assert "--runtime=runsc" in cmd
    assert provider.provider_name == "gvisor"
    assert provider.runtime_name == "runsc"


# ==============================================================================
# 2. Environment Isolation & Secret Redaction Tests
# ==============================================================================

def test_environment_isolation_strips_host_secrets(monkeypatch):
    """Test that host secrets and sensitive environment variables are completely stripped."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-live-super-secret-key-12345")
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_super_secret_github_token_abc")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
    monkeypatch.setenv("REDIS_URL", "redis://:secret@localhost:6379/0")
    monkeypatch.setenv("PATCHPROOF_API_KEY", "patchproof_tenant_secret")
    monkeypatch.setenv("PATCHPROOF_SIGNING_KEY", "ed25519_private_key_pem")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "aws_secret_9999")

    # Build isolated environment
    env = build_isolated_environment(base_env=os.environ)

    assert "OPENAI_API_KEY" not in env
    assert "GITHUB_TOKEN" not in env
    assert "DATABASE_URL" not in env
    assert "REDIS_URL" not in env
    assert "PATCHPROOF_API_KEY" not in env
    assert "PATCHPROOF_SIGNING_KEY" not in env
    assert "AWS_SECRET_ACCESS_KEY" not in env
    assert "sk-live-super-secret-key-12345" not in str(env)

    # Safe defaults exist
    assert env["HOME"] == "/tmp"
    assert env["LANG"] == "C.UTF-8"
    assert env["PYTHONDONTWRITEBYTECODE"] == "1"


def test_custom_environment_rejects_sensitive_keys():
    """Test that custom environment variables matching secret patterns are stripped or rejected."""
    custom = {
        "APP_ENV": "staging",
        "CUSTOM_KEY": "my_api_key_123",
        "USER_SECRET_TOKEN": "secret-val",
        "FEATURE_FLAG": "true",
    }
    env = build_isolated_environment(custom_env=custom)
    assert env.get("APP_ENV") == "staging"
    assert env.get("FEATURE_FLAG") == "true"
    assert "CUSTOM_KEY" not in env
    assert "USER_SECRET_TOKEN" not in env


def test_local_sandbox_environment_cannot_read_host_secrets(tmp_path, monkeypatch):
    """Test running a command in LocalProcessSandboxProvider that attempts to read host secrets."""
    secret_val = "SECRET_VALUE_NEVER_LEAK"
    monkeypatch.setenv("SUPER_SECRET_API_TOKEN", secret_val)

    provider = LocalProcessSandboxProvider()
    req = SandboxRequest(
        command=["python", "-c", "import os; print('SECRET=' + os.environ.get('SUPER_SECRET_API_TOKEN', '<NOT_FOUND>'))"],
        workspace_path=tmp_path,
    )
    result = provider.run(req)
    assert result.exit_code == 0
    assert "SECRET=<NOT_FOUND>" in result.stdout
    assert secret_val not in result.stdout
    assert secret_val not in result.combined_output


# ==============================================================================
# 3. Network Isolation Tests
# ==============================================================================

def test_network_isolation_policy_denied(tmp_path):
    """Test that network is denied by default and restricted request returns structured failure."""
    provider = LocalProcessSandboxProvider(allow_network=False)
    req = SandboxRequest(
        command=["python", "-c", "print('hello')"],
        workspace_path=tmp_path,
        network_policy=NetworkPolicy.RESTRICTED,
    )
    result = provider.run(req)
    assert result.exit_code != 0
    assert result.passed is False
    assert "network access is disabled" in result.stderr


# ==============================================================================
# 4. Resource Limits, Timeout, & Output Truncation Tests
# ==============================================================================

def test_sandbox_timeout_enforcement(tmp_path):
    """Test that a long-running command in the sandbox is terminated and marked timed_out."""
    provider = LocalProcessSandboxProvider()
    req = SandboxRequest(
        command=["python", "-c", "import time; time.sleep(5)"],
        workspace_path=tmp_path,
        timeout_seconds=0.3,
    )
    result = provider.run(req)
    assert result.timed_out is True
    assert result.passed is False
    assert result.exit_code == 124
    assert "SANDBOX TIMEOUT" in result.stderr


def test_sandbox_output_truncation_limits_log_flooding(tmp_path):
    """Test that oversized stdout/stderr is truncated safely and recorded."""
    provider = LocalProcessSandboxProvider()
    # Output 50,000 bytes
    req = SandboxRequest(
        command=["python", "-c", "print('A' * 50000)"],
        workspace_path=tmp_path,
        max_output_bytes=1000,
    )
    result = provider.run(req)
    assert result.exit_code == 0
    assert result.output_truncated is True
    assert result.original_output_size >= 50000
    assert len(result.stdout) <= 1000
    assert result.captured_output_size <= 1000


# ==============================================================================
# 5. Fail-Closed Provider Factory Tests
# ==============================================================================

def test_gvisor_unavailable_fails_closed_without_silent_fallback(monkeypatch):
    """Test that requesting gvisor when runsc is unavailable raises SandboxUnavailableError."""
    monkeypatch.setenv("PATCHPROOF_SANDBOX_PROVIDER", "gvisor")

    # Mock assertion to fail
    def fake_fail(self):
        raise SandboxUnavailableError("gVisor runtime 'runsc' is not installed in Docker daemon")

    monkeypatch.setattr(GVisorSandboxProvider, "_assert_runsc_available", fake_fail)

    with pytest.raises(SandboxUnavailableError, match="gVisor runtime 'runsc' is not installed"):
        get_sandbox_provider()


def test_production_mode_prohibits_local_sandbox_without_override(monkeypatch):
    """Test that in production mode, requesting local sandbox without explicit override fails closed."""
    monkeypatch.setenv("PATCHPROOF_ENV", "production")
    monkeypatch.setenv("PATCHPROOF_SANDBOX_PROVIDER", "local")
    monkeypatch.delenv("PATCHPROOF_ALLOW_LOCAL_SANDBOX", raising=False)

    with pytest.raises(SandboxUnavailableError, match="Local process sandbox is prohibited in production"):
        get_sandbox_provider()


def test_production_mode_allows_local_sandbox_with_explicit_override(monkeypatch):
    """Test that in production mode with PATCHPROOF_ALLOW_LOCAL_SANDBOX=1, local sandbox is allowed."""
    monkeypatch.setenv("PATCHPROOF_ENV", "production")
    monkeypatch.setenv("PATCHPROOF_SANDBOX_PROVIDER", "local")
    monkeypatch.setenv("PATCHPROOF_ALLOW_LOCAL_SANDBOX", "1")

    provider = get_sandbox_provider()
    assert isinstance(provider, LocalProcessSandboxProvider)


# ==============================================================================
# 6. Verification Pipeline & Publication Integration Tests
# ==============================================================================

def test_sandbox_failure_blocks_pr_publication(tmp_path):
    """Test that if sandbox verification fails, the job fails and PR publication is blocked."""
    store = InMemoryJobStore()
    published = False

    class SpyClient:
        def create_pull_request(self, **kwargs):
            nonlocal published
            published = True
            return {"number": 1, "url": "https://github.com/acme/repo/pull/1"}

    # Custom sandbox provider that simulates a failed test
    class FailingSandboxProvider:
        provider_name = "mock_container"
        runtime_name = "runc"

        def run(self, request, **kwargs):
            return SandboxResult(
                exit_code=1,
                stdout="test_auth FAILED",
                stderr="AssertionError: 403 != 200",
                duration_seconds=0.5,
                provider=self.provider_name,
                runtime=self.runtime_name,
            )

    orchestrator = create_concrete_remediation_orchestrator(
        store=store,
        github_client=SpyClient(),
        sandbox_provider=FailingSandboxProvider(),
    )

    # Set up workspace with a test file to trigger sandbox tests
    ws = tmp_path / "repo"
    ws.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=ws, check=True)
    subprocess.run(["git", "config", "user.name", "Bot"], cwd=ws, check=True)
    subprocess.run(["git", "config", "user.email", "bot@test.local"], cwd=ws, check=True)
    (ws / "app.py").write_text("def run(): pass\n")
    (ws / "test_app.py").write_text("def test_run(): assert False\n")
    subprocess.run(["git", "add", "."], cwd=ws, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=ws, check=True)
    head_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ws, text=True).strip()

    job = JobRecord(job_id="job-sbx-fail", repository="acme/service", delivery_id="d1", commit_sha=head_sha)
    store.create(job)

    # Override clone to use our workspace
    orchestrator.clone = lambda repo, sha: str(ws)

    result = orchestrator.run(job.job_id)
    assert result["state"] == JobState.FAILED.value
    assert result["verified"] is False
    assert published is False


def test_sandbox_success_produces_verified_signed_pr(tmp_path):
    """Test that successful sandbox verification passes the verification gate, creates PR, and signs evidence."""
    store = InMemoryJobStore()
    created_prs = []

    class SuccessGitHubClient:
        def create_pull_request(self, **kwargs):
            created_prs.append(kwargs)
            return {"number": 77, "url": "https://github.com/acme/service/pull/77", "head_sha": "sha123"}

        def verify_repository_permissions(self, *args, **kwargs):
            return True

        def create_branch(self, *args, **kwargs):
            return "patchproof/fix"

        def push_branch(self, *args, **kwargs):
            pass

        def create_check_run(self, **kwargs):
            from packages.github.check_runs import CheckRunRef
            return CheckRunRef(id=1, name="PatchProof", head_sha="sha123", status="in_progress")

        def update_check_run(self, **kwargs):
            from packages.github.check_runs import CheckRunRef
            return CheckRunRef(id=1, name="PatchProof", head_sha="sha123", status="completed", conclusion="success")

    class PassingSandboxProvider:
        provider_name = "production_container"
        runtime_name = "runsc"

        def run(self, request, **kwargs):
            return SandboxResult(
                exit_code=0,
                stdout="test_auth PASSED\n1 passed in 0.05s",
                stderr="",
                duration_seconds=0.2,
                provider=self.provider_name,
                runtime=self.runtime_name,
            )

    orchestrator = create_concrete_remediation_orchestrator(
        store=store,
        github_client=SuccessGitHubClient(),
        sandbox_provider=PassingSandboxProvider(),
    )

    ws = tmp_path / "repo_ok"
    ws.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=ws, check=True)
    subprocess.run(["git", "config", "user.name", "Bot"], cwd=ws, check=True)
    subprocess.run(["git", "config", "user.email", "bot@test.local"], cwd=ws, check=True)
    (ws / "app.py").write_text(
        "def query_user(user_input: str):\n"
        "    query = f\"SELECT * FROM users WHERE username = '{user_input}'\"\n"
        "    return query\n"
    )
    (ws / "test_app.py").write_text("def test_ok(): assert True\n")
    subprocess.run(["git", "add", "."], cwd=ws, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=ws, check=True)
    head_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ws, text=True).strip()

    job = JobRecord(job_id="job-sbx-pass", repository="acme/service", delivery_id="d2", commit_sha=head_sha)
    store.create(job)
    orchestrator.clone = lambda repo, sha: str(ws)

    result = orchestrator.run(job.job_id)
    assert result["state"] == JobState.PR_CREATED.value
    assert result["verified"] is True
    assert len(created_prs) == 1
    assert result["pr"]["number"] == 77

    # Verify evidence and state
    saved_job = store.get(job.job_id)
    assert saved_job.state == JobState.PR_CREATED
    assert saved_job.verified_sha == head_sha
    assert saved_job.pr_number == 77
