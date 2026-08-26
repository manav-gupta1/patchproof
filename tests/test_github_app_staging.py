import os
import subprocess
from pathlib import Path
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from packages.gitops.staging import WorkspaceStaging, GitOpsError
from packages.github.auth import (
    GitHubAppAuth,
    GitHubAppCredentials,
    InstallationToken,
)
from packages.jobs.state import JobRecord, JobState, JobStateMachine
from packages.jobs.store import InMemoryJobStore
from packages.store.postgres import PostgresJobStore
from packages.webhooks.handlers import WebhookDispatcher
from packages.jobs.pipeline_factory import create_concrete_remediation_orchestrator


@pytest.fixture
def rsa_key_pem():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()


class MockGitHubAppAuth:
    def __init__(self, token_value: str = "ghs_mockinstallationtoken1234567890"):
        self.token_value = token_value
        self.installation_id_requested = None

    def installation_token(self, installation_id: int) -> InstallationToken:
        self.installation_id_requested = installation_id
        return InstallationToken(token=self.token_value, expires_at=int(1e9))


def test_remote_staging_with_github_app_auth(tmp_path):
    """Test remote repository staging uses installation token and scrubs remote URL."""
    # Create a bare upstream remote git repo to simulate github.com/octocat/repo
    upstream_repo = tmp_path / "upstream.git"
    upstream_repo.mkdir(parents=True)
    subprocess.run(["git", "init", "--bare", "-q"], cwd=upstream_repo, check=True)

    # Initialize a commit in a working tree and push to upstream
    work_repo = tmp_path / "work"
    work_repo.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=work_repo, check=True)
    subprocess.run(["git", "config", "user.name", "Octocat"], cwd=work_repo, check=True)
    subprocess.run(["git", "config", "user.email", "octocat@github.local"], cwd=work_repo, check=True)
    (work_repo / "app.py").write_text("def app(): pass\n")
    subprocess.run(["git", "add", "."], cwd=work_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "initial commit"], cwd=work_repo, check=True)
    subprocess.run(["git", "remote", "add", "origin", str(upstream_repo)], cwd=work_repo, check=True)
    subprocess.run(["git", "push", "-q", "origin", "HEAD:main"], cwd=work_repo, check=True)
    head_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=work_repo, text=True).strip()

    # Monkeypatch git checkout command to clone from our local bare repo instead of github.com
    secret_token = "ghs_secretinstallationtoken999999"
    auth = MockGitHubAppAuth(token_value=secret_token)
    staging = WorkspaceStaging(auth=auth)

    # Custom staging override for local test simulation
    def fake_try_clone(temp_dir, repo, commit_sha, inst_id):
        token = auth.installation_token(inst_id or 1).token
        auth_url = f"file://{upstream_repo}"
        clean_url = f"https://github.com/{repo}.git"

        subprocess.run(["git", "init", "-q"], cwd=temp_dir, check=True)
        subprocess.run(["git", "remote", "add", "origin", auth_url], cwd=temp_dir, check=True)
        subprocess.run(["git", "fetch", "--depth=1", "origin", commit_sha or "main"], cwd=temp_dir, check=True)
        subprocess.run(["git", "checkout", "-q", "--detach", "FETCH_HEAD"], cwd=temp_dir, check=True)
        # Scrub remote URL
        subprocess.run(["git", "remote", "set-url", "origin", clean_url], cwd=temp_dir, check=True)
        return True

    staging._try_clone_remote_repo = fake_try_clone

    workspace = staging.stage(
        repository="octocat/remote-repo",
        commit_sha=head_sha,
        installation_id=42,
    )

    try:
        assert workspace.path.exists()
        assert (workspace.path / "app.py").exists()
        assert (workspace.path / "app.py").read_text() == "def app(): pass\n"

        # Verify git remote URL has been sanitized and does NOT contain the secret token
        remotes = subprocess.check_output(["git", "remote", "-v"], cwd=workspace.path, text=True)
        assert secret_token not in remotes
        assert "https://github.com/octocat/remote-repo.git" in remotes
        assert auth.installation_id_requested == 42
    finally:
        workspace.cleanup()


def test_remote_staging_token_scrubbed_on_failure(tmp_path):
    """Test that git checkout failure scrubs secret tokens from exception message."""
    secret_token = "ghs_supersecretinstallationtoken12345"
    auth = MockGitHubAppAuth(token_value=secret_token)
    staging = WorkspaceStaging(auth=auth)

    # Force a failure with invalid commit SHA
    with pytest.raises(GitOpsError) as excinfo:
        staging.stage(
            repository="example/nonexistent-repo",
            commit_sha="baddeadbeef12345",
            installation_id=1,
        )

    err_msg = str(excinfo.value)
    assert secret_token not in err_msg
    assert "[REDACTED]" in err_msg or "failed" in err_msg.lower()


def test_remote_staging_offline_fallback_without_credentials():
    """Test that staging a remote repository without credentials initializes clean fixture repo."""
    staging = WorkspaceStaging()
    workspace = staging.stage(repository="fixture/test-repo", commit_sha="HEAD")

    try:
        assert workspace.path.exists()
        assert (workspace.path / "app.py").exists()
        assert "def handle_request" in (workspace.path / "app.py").read_text()
    finally:
        workspace.cleanup()


def test_webhook_dispatcher_extracts_installation_id():
    """Test that WebhookDispatcher parses installation.id and passes it to the job store."""
    store = InMemoryJobStore()
    dispatcher = WebhookDispatcher(jobs=store, enqueue=lambda job_id: None)

    class MockEvent:
        event = "pull_request"
        delivery_id = "deliv-inst-test-001"
        payload = {
            "repository": {"full_name": "acme/repo"},
            "pull_request": {"head": {"sha": "c" * 40}},
            "installation": {"id": 98765},
        }

    res = dispatcher.dispatch(MockEvent())
    assert res["accepted"] is True

    job = store.get(res["job_id"])
    assert job is not None
    assert job.installation_id == 98765
    assert job.repository == "acme/repo"


def test_postgres_store_persists_installation_id():
    """Test that PostgresJobStore saves and retrieves installation_id."""
    store = PostgresJobStore("sqlite:///:memory:")
    store.create_schema()

    job = store.create_from_webhook(
        delivery_id="deliv-pg-inst-001",
        repository="acme/pg-repo",
        commit_sha="d" * 40,
        event_type="pull_request",
        installation_id=54321,
    )

    assert job.installation_id == 54321

    retrieved = store.get(job.job_id)
    assert retrieved is not None
    assert retrieved.installation_id == 54321
    assert retrieved.repository == "acme/pg-repo"


def test_full_pipeline_with_github_app_staging_and_publisher(tmp_path):
    """Test concrete remediation orchestrator with GitHub App staging and publication."""
    source_repo = tmp_path / "app_pipeline_repo"
    source_repo.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=source_repo, check=True)
    subprocess.run(["git", "config", "user.name", "Bot"], cwd=source_repo, check=True)
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

    class MockPublisherClient:
        def __init__(self):
            self.created_prs = []

        def create_pull_request(self, **kwargs):
            self.created_prs.append(kwargs)
            return {
                "number": 101,
                "url": f"https://github.com/{kwargs['repository']}/pull/101",
                "head_sha": head_sha,
            }

    store = InMemoryJobStore()
    job = JobRecord(
        job_id="job-gh-app-pipeline-001",
        repository=str(source_repo),
        delivery_id="deliv-gh-app-pipe",
        commit_sha=head_sha,
        installation_id=777,
    )
    store.create(job)

    mock_client = MockPublisherClient()
    orchestrator = create_concrete_remediation_orchestrator(
        store=store,
        github_client=mock_client,
    )

    result = orchestrator.run(job.job_id)

    assert result["state"] == JobState.PR_CREATED.value
    assert result["verified"] is True
    assert result["pr"]["number"] == 101
    assert result["pr"]["url"] == f"https://github.com/{source_repo}/pull/101"
    assert len(mock_client.created_prs) == 1
    assert mock_client.created_prs[0]["installation_id"] == 777
