import os
import subprocess
import time
from pathlib import Path
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import jwt

from packages.github.auth import (
    GitHubAppAuth,
    GitHubAppCredentials,
    GitHubAuthError,
    InstallationToken,
    create_app_jwt,
)
from packages.github.client import GitHubAppClient, PullRequestRef
from packages.github.publisher import GitHubPublisher, PublicationRejected
from packages.github.transport import GitHubAPIError, RequestsGitHubTransport
from packages.jobs.orchestrator import RemediationOrchestrator
from packages.jobs.pipeline_factory import (
    create_concrete_remediation_orchestrator,
    ConcreteGitHubPublisher,
)
from packages.jobs.state import JobState, JobStateMachine, JobRecord
from packages.jobs.store import InMemoryJobStore


@pytest.fixture
def rsa_key_pem():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()


def test_github_app_jwt_generation_and_claims(rsa_key_pem):
    """Test generating a valid RS256 JWT for GitHub App authentication."""
    app_id = "98765"
    token = create_app_jwt(app_id=app_id, private_key_pem=rsa_key_pem)

    # Decode and verify header and payload
    unverified_header = jwt.get_unverified_header(token)
    assert unverified_header["alg"] == "RS256"
    assert unverified_header["typ"] == "JWT"

    pub_key = serialization.load_pem_private_key(rsa_key_pem.encode(), password=None).public_key()
    decoded = jwt.decode(
        token,
        pub_key,
        algorithms=["RS256"],
    )
    assert decoded["iss"] == "98765"
    assert decoded["exp"] > decoded["iat"]
    assert decoded["exp"] - decoded["iat"] <= 660


def test_github_app_credentials_from_env_and_masking(rsa_key_pem, monkeypatch, tmp_path):
    """Test credential loading from env and secret masking."""
    monkeypatch.setenv("GITHUB_APP_ID", "12345")
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", rsa_key_pem)
    monkeypatch.setenv("GITHUB_APP_INSTALLATION_ID", "67890")

    creds = GitHubAppCredentials.from_env()
    assert creds.app_id == "12345"
    assert creds.installation_id == 67890
    assert rsa_key_pem not in repr(creds)
    assert "[REDACTED]" in repr(creds)
    assert rsa_key_pem not in str(creds)

    # Test loading from private key path
    key_file = tmp_path / "github_app.pem"
    key_file.write_text(rsa_key_pem)
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY")
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY_PATH", str(key_file))

    creds_from_file = GitHubAppCredentials.from_env()
    assert creds_from_file.app_id == "12345"
    assert creds_from_file.private_key_pem.strip() == rsa_key_pem.strip()


def test_missing_credentials_raises_clear_error(monkeypatch):
    """Test that missing required credentials raises descriptive GitHubAuthError."""
    monkeypatch.delenv("GITHUB_APP_ID", raising=False)
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY_PATH", raising=False)

    with pytest.raises(GitHubAuthError, match="Missing required GITHUB_APP_ID"):
        GitHubAppCredentials.from_env()


def test_github_app_auth_installation_token_acquisition_and_caching(rsa_key_pem):
    """Test obtaining an installation token via fake provider and caching."""
    token_fetch_count = 0

    class FakeClient:
        def create_app_jwt(self, **kwargs):
            return "fake-jwt"

        def create_installation_token(self, **kwargs):
            nonlocal token_fetch_count
            token_fetch_count += 1
            return {
                "token": f"ghs_fake_token_{token_fetch_count}",
                "expires_at": int(time.time()) + 3600,
            }

    auth = GitHubAppAuth(app_id="123", private_key_pem=rsa_key_pem, github_client=FakeClient())
    token1 = auth.installation_token(installation_id=456)
    assert token1.token == "ghs_fake_token_1"
    assert not token1.expired
    assert "[REDACTED]" in repr(token1) or "..." in repr(token1)

    # Second call should use cached token
    token2 = auth.installation_token(installation_id=456)
    assert token2.token == "ghs_fake_token_1"
    assert token_fetch_count == 1


def test_github_app_client_pr_creation_success(rsa_key_pem):
    """Test successful PR creation via GitHubAppClient."""
    class FakeTransport:
        def __init__(self):
            self.created_prs = []

        def find_pull_request_by_marker(self, **kwargs):
            return None

        def find_pull_request_by_branch(self, **kwargs):
            return None

        def create_pull_request(self, **kwargs):
            self.created_prs.append(kwargs)
            return {
                "number": 101,
                "html_url": "https://github.com/acme/repo/pull/101",
                "head": {"sha": "head-sha-123"},
            }

    class FakeAuth:
        def installation_token(self, installation_id):
            return InstallationToken(token="ghs_secret_access_token_123", expires_at=int(time.time()) + 3600)

    transport = FakeTransport()
    client = GitHubAppClient(auth=FakeAuth(), transport=transport)

    ref = client.create_pull_request(
        installation_id=456,
        repository="acme/repo",
        head="patchproof/fix-sqli",
        base="main",
        title="fix(security): sanitize user input",
        body="Automated security patch.",
    )

    assert isinstance(ref, PullRequestRef)
    assert ref.number == 101
    assert ref.url == "https://github.com/acme/repo/pull/101"
    assert ref.branch == "patchproof/fix-sqli"
    assert ref.base_branch == "main"
    assert ref.repository == "acme/repo"
    assert len(transport.created_prs) == 1
    assert transport.created_prs[0]["token"] == "ghs_secret_access_token_123"


def test_github_app_client_pr_idempotency():
    """Test that PR creation is idempotent when PR already exists."""
    class FakeTransport:
        def find_pull_request_by_marker(self, *, marker, **kwargs):
            if "patchproof:job-123" in marker:
                return {
                    "number": 42,
                    "html_url": "https://github.com/acme/repo/pull/42",
                    "head": {"sha": "sha-42"},
                }
            return None

        def create_pull_request(self, **kwargs):
            raise AssertionError("create_pull_request should not be called when PR exists")

    class FakeAuth:
        def installation_token(self, installation_id):
            return InstallationToken(token="token", expires_at=int(time.time()) + 3600)

    client = GitHubAppClient(auth=FakeAuth(), transport=FakeTransport())
    ref = client.create_pull_request(
        installation_id=1,
        repository="acme/repo",
        head="patchproof/fix",
        base="main",
        title="fix",
        body="body",
        idempotency_key="patchproof:job-123",
    )
    assert ref.number == 42
    assert ref.url == "https://github.com/acme/repo/pull/42"


def test_github_app_client_error_handling_and_secret_masking():
    """Test error handling for permission denied and repository not found without leaking secrets."""
    secret_token = "ghs_super_secret_token_abc123xyz"

    class FailingTransport:
        def find_pull_request_by_marker(self, **kwargs):
            return None

        def find_pull_request_by_branch(self, **kwargs):
            return None

        def create_pull_request(self, **kwargs):
            raise RuntimeError(f"HTTP 403 Forbidden with token {secret_token}: Resource not accessible by integration")

    class FakeAuth:
        def installation_token(self, installation_id):
            return InstallationToken(token=secret_token, expires_at=int(time.time()) + 3600)

    client = GitHubAppClient(auth=FakeAuth(), transport=FailingTransport())

    with pytest.raises(GitHubAPIError) as exc_info:
        client.create_pull_request(
            installation_id=1,
            repository="acme/forbidden-repo",
            head="patchproof/fix",
            base="main",
            title="fix",
            body="body",
        )

    err_msg = str(exc_info.value)
    assert secret_token not in err_msg
    assert "[REDACTED]" in err_msg


def test_verification_failure_blocks_github_publication():
    """Test that unverified remediation never attempts GitHub publication."""
    published = False

    class SpyClient:
        def create_pull_request(self, **kwargs):
            nonlocal published
            published = True
            return {"number": 1, "url": "https://github.com/acme/repo/pull/1"}

    publisher = ConcreteGitHubPublisher(client=SpyClient())

    job = JobRecord(job_id="job-unverified-1", repository="acme/repo", delivery_id="d-1", commit_sha="sha1")
    patch_result = {"head_branch": "patchproof/fix", "title": "fix"}
    failed_evidence = {"verified": False, "evidence_id": "ev-1"}

    with pytest.raises(PermissionError, match="refusing to publish unverified remediation"):
        publisher.publish_verified(job=job, patch_result=patch_result, evidence=failed_evidence)

    assert not published


def test_remediation_orchestrator_with_github_app_integration(tmp_path):
    """End-to-end test of remediation orchestrator with GitHub App publication."""
    # Create test repository
    source_repo = tmp_path / "app_repo"
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

    class FakeGitHubClient:
        def __init__(self):
            self.created = []

        def create_pull_request(self, **kwargs):
            self.created.append(kwargs)
            return {
                "number": 99,
                "html_url": f"https://github.com/{kwargs.get('repository')}/pull/99",
                "head_sha": head_sha,
            }

    fake_github = FakeGitHubClient()
    store = InMemoryJobStore()
    job = JobRecord(
        job_id="job-gh-e2e-001",
        repository="example/remediation-target",
        delivery_id="delivery-gh-001",
        commit_sha=head_sha,
    )
    store.create(job)

    orchestrator = create_concrete_remediation_orchestrator(
        store=store,
        github_client=fake_github,
    )

    result = orchestrator.run(job.job_id)

    assert result["state"] == JobState.PR_CREATED.value
    assert result["verified"] is True
    assert result["job_id"] == "job-gh-e2e-001"
    assert result["pr"]["number"] == 99
    assert "https://github.com/example/remediation-target/pull/99" in result["pr"]["url"]
    assert len(fake_github.created) == 1
    assert fake_github.created[0]["repository"] == "example/remediation-target"


def test_github_app_client_push_branch_failure_redacts_secrets(tmp_path, monkeypatch):
    """Test that git push failure sanitizes access tokens from exceptions."""
    secret_token = "ghs_sensitive_access_token_987654321"

    class FakeAuth:
        def installation_token(self, installation_id):
            return InstallationToken(token=secret_token, expires_at=int(time.time()) + 3600)

    client = GitHubAppClient(auth=FakeAuth())
    ws_dir = tmp_path / "ws"
    ws_dir.mkdir()

    # Simulate git push failure
    def fake_subprocess_run(cmd, **kwargs):
        class Result:
            returncode = 128
            stderr = f"fatal: unable to access 'https://x-access-token:{secret_token}@github.com/acme/repo.git/': The requested URL returned error: 403"
            stdout = ""
        return Result()

    monkeypatch.setattr(subprocess, "run", fake_subprocess_run)

    with pytest.raises(GitHubAPIError) as exc_info:
        client.push_branch(
            workspace_path=ws_dir,
            repository="acme/repo",
            branch="patchproof/fix",
            installation_id=1,
        )

    err_str = str(exc_info.value)
    assert secret_token not in err_str
    assert "[REDACTED]" in err_str


def test_publication_failure_marks_job_failed_and_preserves_audit_trail(tmp_path):
    """Test that failure in GitHub publication stage transitions job to FAILED in store."""
    source_repo = tmp_path / "pub_fail_repo"
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

    class ExplodingGitHubClient:
        def create_pull_request(self, **kwargs):
            raise GitHubAPIError("GitHub API 500: Internal Server Error during PR creation")

    store = InMemoryJobStore()
    job = JobRecord(
        job_id="job-pub-fail-001",
        repository=str(source_repo),
        delivery_id="delivery-pub-fail-001",
        commit_sha=head_sha,
    )
    store.create(job)

    orchestrator = create_concrete_remediation_orchestrator(
        store=store,
        github_client=ExplodingGitHubClient(),
    )

    result = orchestrator.run(job.job_id)

    assert result["state"] == JobState.FAILED.value
    assert result["verified"] is False
    assert "Internal Server Error" in result["error"]

    # Store state must be FAILED
    stored_job = store.get(job.job_id)
    assert stored_job.state == JobState.FAILED


def test_sanitize_secret_text_scrubs_sensitive_patterns(rsa_key_pem):
    """Test that sanitize_secret_text scrubs all classes of credentials."""
    from packages.github.auth import sanitize_secret_text

    raw_text = (
        f"Error connecting with {rsa_key_pem} and token ghs_1234567890abcdef123456 "
        f"at https://x-access-token:ghs_secret@github.com/org/repo.git with Bearer eyJhbGciOiJSUzI1NiJ9.test.sig"
    )
    scrubbed = sanitize_secret_text(raw_text)

    assert rsa_key_pem not in scrubbed
    assert "[REDACTED_PRIVATE_KEY]" in scrubbed
    assert "ghs_1234567890abcdef123456" not in scrubbed
    assert "[REDACTED_TOKEN]" in scrubbed
    assert "https://[REDACTED_AUTH]@github.com" in scrubbed
    assert "Bearer [REDACTED_JWT]" in scrubbed

