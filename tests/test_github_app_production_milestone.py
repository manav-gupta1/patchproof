from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from typing import Any
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
    sanitize_secret_text,
)
from packages.github.client import GitHubAppClient, PullRequestRef
from packages.github.transport import (
    GitHubAPIError,
    GitHubConflictError,
    GitHubNotFoundError,
    GitHubPermissionError,
    GitHubRateLimitError,
    GitHubServerError,
    GitHubUnprocessableError,
    RequestsGitHubTransport,
)
from packages.github.check_runs import GitHubCheckRunReporter, CheckRunRef
from packages.jobs.orchestrator import RemediationOrchestrator
from packages.jobs.pipeline_factory import (
    ConcreteGitHubPublisher,
    create_concrete_remediation_orchestrator,
)
from packages.jobs.state import JobRecord, JobState, JobStateMachine
from packages.jobs.store import InMemoryJobStore
from packages.lifecycle.manager import PRLifecycleManager
from packages.signing import Ed25519EvidenceSigner


@pytest.fixture
def rsa_key_pem():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()


# ==============================================================================
# 1. Authentication Tests
# ==============================================================================

def test_jwt_generation_and_claims(rsa_key_pem):
    app_id = "123456"
    token = create_app_jwt(app_id=app_id, private_key_pem=rsa_key_pem)

    header = jwt.get_unverified_header(token)
    assert header["alg"] == "RS256"

    pub_key = serialization.load_pem_private_key(rsa_key_pem.encode(), password=None).public_key()
    decoded = jwt.decode(token, pub_key, algorithms=["RS256"])
    assert decoded["iss"] == "123456"
    assert decoded["exp"] > decoded["iat"]
    assert decoded["exp"] - decoded["iat"] <= 660


def test_jwt_generation_malformed_key_fails_cleanly():
    with pytest.raises(GitHubAuthError, match="Invalid or missing RSA private key"):
        create_app_jwt(app_id="123", private_key_pem="not-a-pem-key")


def test_credentials_from_env_and_path(rsa_key_pem, monkeypatch, tmp_path):
    key_file = tmp_path / "app_private.pem"
    key_file.write_text(rsa_key_pem)

    monkeypatch.setenv("GITHUB_APP_ID", "998877")
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY", raising=False)
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY_PATH", str(key_file))
    monkeypatch.setenv("GITHUB_APP_INSTALLATION_ID", "445566")

    creds = GitHubAppCredentials.from_env()
    assert creds.app_id == "998877"
    assert creds.installation_id == 445566
    assert creds.private_key_pem.strip() == rsa_key_pem.strip()

    # Secret masking in str and repr
    assert rsa_key_pem not in repr(creds)
    assert "[REDACTED]" in repr(creds)


def test_token_caching_and_expired_refresh(rsa_key_pem):
    call_count = 0

    class FakeClient:
        def create_app_jwt(self, **kwargs):
            return "fake-jwt"

        def create_installation_token(self, **kwargs):
            nonlocal call_count
            call_count += 1
            # First token expires immediately, second is long-lived
            ttl = 10 if call_count == 1 else 3600
            return {
                "token": f"ghs_token_version_{call_count}",
                "expires_at": int(time.time()) + ttl,
            }

    auth = GitHubAppAuth(app_id="123", private_key_pem=rsa_key_pem, github_client=FakeClient())

    # 1. Fetch first token (which has TTL <= 60s, so it is considered expired for safety)
    tok1 = auth.installation_token(installation_id=101)
    assert tok1.token == "ghs_token_version_1"
    assert tok1.expired is True

    # 2. Fetching again must trigger automatic refresh since tok1 is expired
    tok2 = auth.installation_token(installation_id=101)
    assert tok2.token == "ghs_token_version_2"
    assert tok2.expired is False
    assert call_count == 2

    # 3. Fetching third time must use cache
    tok3 = auth.installation_token(installation_id=101)
    assert tok3.token == "ghs_token_version_2"
    assert call_count == 2


def test_token_caching_thread_safety(rsa_key_pem):
    fetch_count = 0

    class ConcurrentClient:
        def create_app_jwt(self, **kwargs):
            return "jwt-thread"

        def create_installation_token(self, **kwargs):
            nonlocal fetch_count
            time.sleep(0.01)
            fetch_count += 1
            return {
                "token": "ghs_thread_safe_token",
                "expires_at": int(time.time()) + 3600,
            }

    auth = GitHubAppAuth(app_id="123", private_key_pem=rsa_key_pem, github_client=ConcurrentClient())

    threads = []
    tokens = []

    def worker():
        t = auth.installation_token(installation_id=202)
        tokens.append(t.token)

    for _ in range(10):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    assert len(tokens) == 10
    assert all(tok == "ghs_thread_safe_token" for tok in tokens)
    assert fetch_count == 1


def test_secret_sanitization():
    raw = "Error with private key -----BEGIN RSA PRIVATE KEY-----\nMIIEogIBAAKCAQEA...\n-----END RSA PRIVATE KEY----- and token ghs_1234567890abcdef123 and url https://x-access-token:ghs_secret@github.com/org/repo.git"
    sanitized = sanitize_secret_text(raw)
    assert "-----BEGIN" not in sanitized
    assert "[REDACTED_PRIVATE_KEY]" in sanitized
    assert "ghs_1234567890abcdef123" not in sanitized
    assert "[REDACTED_TOKEN]" in sanitized
    assert "ghs_secret" not in sanitized
    assert "[REDACTED_AUTH]" in sanitized


# ==============================================================================
# 2. Authorization Tests
# ==============================================================================

def test_authorization_repository_accessible(rsa_key_pem):
    class AuthTransport:
        def get_repository(self, *, token, owner, repo):
            return {
                "full_name": f"{owner}/{repo}",
                "permissions": {"admin": True, "push": True, "pull": True},
            }

    class FakeAuth:
        def installation_token(self, inst_id):
            return InstallationToken(token="ghs_auth_tok", expires_at=int(time.time()) + 3600)

    client = GitHubAppClient(auth=FakeAuth(), transport=AuthTransport())
    assert client.verify_repository_permissions("acme/service") is True


def test_authorization_repository_not_found_fails_closed():
    class NotFoundTransport:
        def get_repository(self, *, token, owner, repo):
            raise GitHubNotFoundError("Repository not found")

    class FakeAuth:
        def installation_token(self, inst_id):
            return InstallationToken(token="ghs_auth_tok", expires_at=int(time.time()) + 3600)

    client = GitHubAppClient(auth=FakeAuth(), transport=NotFoundTransport())
    with pytest.raises(GitHubPermissionError, match="not accessible or not found"):
        client.verify_repository_permissions("acme/secret-service")


def test_authorization_insufficient_permissions_fails_closed():
    class ReadOnlyTransport:
        def get_repository(self, *, token, owner, repo):
            return {
                "full_name": f"{owner}/{repo}",
                "permissions": {"admin": False, "push": False, "pull": True},
            }

    class FakeAuth:
        def installation_token(self, inst_id):
            return InstallationToken(token="ghs_auth_tok", expires_at=int(time.time()) + 3600)

    client = GitHubAppClient(auth=FakeAuth(), transport=ReadOnlyTransport())
    with pytest.raises(GitHubPermissionError, match="Missing required repository permission"):
        client.verify_repository_permissions("acme/readonly-service", required_permissions=["push"])


# ==============================================================================
# 3. Transport & API Client Tests
# ==============================================================================

def test_transport_typed_errors_and_methods():
    class MockSession:
        def __init__(self):
            self.calls = []

        def get(self, url, **kwargs):
            self.calls.append(("GET", url, kwargs))
            if "pulls/10" in url:
                return self._resp({"number": 10, "html_url": "https://github.com/acme/repo/pull/10", "head": {"sha": "sha10"}})
            if "git/ref/heads/feature" in url:
                return self._resp({"ref": "refs/heads/feature", "object": {"sha": "sha-ref"}})
            if "commits/sha123" in url:
                return self._resp({"sha": "sha123", "commit": {"message": "feat: init"}})
            return self._resp({})

        def post(self, url, **kwargs):
            self.calls.append(("POST", url, kwargs))
            if "git/refs" in url:
                return self._resp({"ref": kwargs.get("json", {}).get("ref"), "object": {"sha": kwargs.get("json", {}).get("sha")}})
            if "pulls" in url:
                return self._resp({"number": 99, "html_url": "https://github.com/acme/repo/pull/99", "head": {"sha": "head99"}})
            if "check-runs" in url:
                return self._resp({"id": 555, "name": "PatchProof", "status": "in_progress", "head_sha": "sha1"})
            return self._resp({})

        def patch(self, url, **kwargs):
            self.calls.append(("PATCH", url, kwargs))
            if "check-runs/555" in url:
                return self._resp({"id": 555, "name": "PatchProof", "status": "completed", "conclusion": "success"})
            if "pulls/99" in url:
                return self._resp({"number": 99, "title": kwargs.get("json", {}).get("title")})
            return self._resp({})

        def _resp(self, data):
            class R:
                def raise_for_status(self): pass
                def json(self): return data
            return R()

    transport = RequestsGitHubTransport(session=MockSession())

    # get_pull_request
    pr = transport.get_pull_request(token="tok", owner="acme", repo="repo", pr_number=10)
    assert pr["number"] == 10

    # get_ref
    ref = transport.get_ref(token="tok", owner="acme", repo="repo", ref="heads/feature")
    assert ref["ref"] == "refs/heads/feature"

    # create_ref
    new_ref = transport.create_ref(token="tok", owner="acme", repo="repo", ref="heads/fix", sha="sha123")
    assert new_ref["ref"] == "refs/heads/fix"

    # get_commit
    commit = transport.get_commit(token="tok", owner="acme", repo="repo", commit_sha="sha123")
    assert commit["sha"] == "sha123"

    # create_check_run & update_check_run
    cr = transport.create_check_run(token="tok", owner="acme", repo="repo", name="PatchProof", head_sha="sha1")
    assert cr["id"] == 555
    up_cr = transport.update_check_run(token="tok", owner="acme", repo="repo", check_run_id=555, status="completed", conclusion="success")
    assert up_cr["conclusion"] == "success"


# ==============================================================================
# 4. Publication, Branch Safety, & Idempotency Tests
# ==============================================================================

def test_branch_safety_rejects_protected_branches():
    client = GitHubAppClient(auth=lambda: None)
    with pytest.raises(GitHubPermissionError, match="Cannot overwrite protected branch"):
        client.create_branch("acme/repo", "main", "sha123")

    with pytest.raises(GitHubPermissionError, match="protected branch"):
        client.push_branch(workspace_path="/tmp", repository="acme/repo", branch="master")

    with pytest.raises(GitHubPermissionError, match="protected branch"):
        client.create_pull_request(repository="acme/repo", head="main", base="main")


def test_pr_creation_with_race_condition_fallback():
    class ConflictTransport:
        def __init__(self):
            self.created = False

        def find_pull_request_by_marker(self, **kwargs):
            if self.created:
                return {"number": 88, "html_url": "https://github.com/acme/repo/pull/88", "head": {"sha": "sha88"}}
            return None

        def find_pull_request_by_branch(self, **kwargs):
            return None

        def create_pull_request(self, **kwargs):
            self.created = True
            # Simulate a 422 because PR was created concurrently
            raise GitHubUnprocessableError("A pull request already exists for acme:patchproof/fix.")

    class FakeAuth:
        def installation_token(self, inst_id):
            return InstallationToken(token="ghs_tok", expires_at=int(time.time()) + 3600)

    client = GitHubAppClient(auth=FakeAuth(), transport=ConflictTransport())
    pr = client.create_pull_request(
        repository="acme/repo",
        head="patchproof/fix",
        base="main",
        title="fix(security)",
        idempotency_key="patchproof:marker-88",
    )
    assert pr.number == 88
    assert pr.url == "https://github.com/acme/repo/pull/88"


# ==============================================================================
# 5. Check Runs Integration Tests
# ==============================================================================

def test_check_run_reporter_lifecycle():
    class CheckRunClient:
        def __init__(self):
            self.check_runs = {}
            self._next_id = 1000

        def create_check_run(self, **kwargs):
            cid = self._next_id
            self._next_id += 1
            cr = CheckRunRef(
                id=cid,
                name=kwargs.get("name", "PatchProof"),
                head_sha=kwargs["head_sha"],
                status=kwargs.get("status", "queued"),
                conclusion=kwargs.get("conclusion"),
                html_url=f"https://github.com/{kwargs['repository']}/runs/{cid}",
            )
            self.check_runs[cid] = cr
            return cr

        def update_check_run(self, **kwargs):
            cid = kwargs["check_run_id"]
            existing = self.check_runs[cid]
            updated = CheckRunRef(
                id=cid,
                name=existing.name,
                head_sha=existing.head_sha,
                status=kwargs.get("status", "completed"),
                conclusion=kwargs.get("conclusion", existing.conclusion),
                html_url=existing.html_url,
            )
            self.check_runs[cid] = updated
            return updated

    client = CheckRunClient()
    reporter = GitHubCheckRunReporter(client=client)

    job = JobRecord(job_id="job-cr-test", repository="acme/service", commit_sha="head12345", delivery_id="d1")

    # 1. Queued
    cr_q = reporter.report_queued(job)
    assert cr_q.status == "queued"

    # 2. In progress
    cr_p = reporter.report_in_progress(job, check_run_id=cr_q.id)
    assert cr_p.status == "in_progress"

    # 3. Success
    evidence = {
        "verified": True,
        "evidence_id": "ev-cr-1",
        "signature": "sig9999",
        "signer": "Ed25519",
    }
    pr = {"number": 7, "url": "https://github.com/acme/service/pull/7"}
    cr_s = reporter.report_success(job, check_run_id=cr_q.id, pr=pr, evidence=evidence)
    assert cr_s.status == "completed"
    assert cr_s.conclusion == "success"


# ==============================================================================
# 6. Full End-to-End Fake GitHub Pipeline Test
# ==============================================================================

def test_full_e2e_github_app_pipeline():
    store = InMemoryJobStore()
    signer = Ed25519EvidenceSigner(key_id="dev-key-1")

    class E2EFakeGitHubClient:
        def __init__(self):
            self.created_prs = []
            self.check_runs = []
            self.pushed_branches = []

        def verify_repository_permissions(self, repository, installation_id=None):
            return True

        def create_branch(self, repository, branch, base_sha, installation_id=None):
            return branch

        def push_branch(self, **kwargs):
            self.pushed_branches.append(kwargs)

        def create_pull_request(self, **kwargs):
            pr_data = {
                "number": len(self.created_prs) + 1,
                "url": f"https://github.com/{kwargs['repository']}/pull/{len(self.created_prs) + 1}",
                "head_sha": "head-sha-final",
                "repository": kwargs["repository"],
                "branch": kwargs["head"],
                "base_branch": kwargs["base"],
            }
            self.created_prs.append(pr_data)
            return PullRequestRef(
                number=pr_data["number"],
                url=pr_data["url"],
                head_sha=pr_data["head_sha"],
                branch=pr_data["branch"],
                base_branch=pr_data["base_branch"],
                repository=pr_data["repository"],
            )

        def create_check_run(self, **kwargs):
            cr = CheckRunRef(
                id=101,
                name="PatchProof Security Remediation",
                head_sha=kwargs["head_sha"],
                status=kwargs.get("status", "queued"),
                conclusion=kwargs.get("conclusion"),
                html_url="https://github.com/acme/app/runs/101",
            )
            self.check_runs.append(cr)
            return cr

        def update_check_run(self, **kwargs):
            cr = CheckRunRef(
                id=kwargs["check_run_id"],
                name="PatchProof Security Remediation",
                head_sha="head123",
                status=kwargs.get("status", "completed"),
                conclusion=kwargs.get("conclusion", "success"),
                html_url="https://github.com/acme/app/runs/101",
            )
            self.check_runs.append(cr)
            return cr

    fake_gh = E2EFakeGitHubClient()
    reporter = GitHubCheckRunReporter(client=fake_gh)

    job = JobRecord(
        job_id="job-e2e-gh",
        repository="acme/app",
        delivery_id="deliv-e2e-gh",
        commit_sha="a"*40,
        target_branch="main",
        installation_id=999,
    )
    store.create(job)

    class MockVerification:
        verified = True
        findings = []

    orchestrator = RemediationOrchestrator(
        store=store,
        state_machine=JobStateMachine(),
        clone=lambda repo, sha: "/tmp/fake-workspace",
        scan=lambda ws: [{"rule_id": "rule-sqli", "severity": "HIGH", "fingerprint": "fp123"}],
        analyze=lambda ws, f: {"candidate": None, "finding": f[0], "context": None},
        patch=lambda ws, p: {
            "applied_files": ["main.py"],
            "diff": "--- a/main.py\n+++ b/main.py",
            "rule_id": "rule-sqli",
            "title": "fix(security): sanitize sql query",
            "explanation": "Replaces string formatting with parameterized query.",
            "head_branch": "patchproof/fix-sqli-fp123",
            "base_branch": "main",
        },
        verify=lambda **kwargs: MockVerification(),
        evidence=lambda *args, **kwargs: signer.sign({
            "job_id": job.job_id,
            "repository": job.repository,
            "commit_sha": job.commit_sha,
            "verified": True,
            "evidence_id": "ev-e2e-1",
            "findings": [{"rule_id": "rule-sqli", "severity": "HIGH"}],
        }),
        github=ConcreteGitHubPublisher(client=fake_gh, installation_id=999),
        check_runs=reporter,
    )

    result = orchestrator.run("job-e2e-gh")
    assert result["state"] == JobState.PR_CREATED.value
    assert result["verified"] is True
    assert result["pr"]["number"] == 1
    assert "patchproof/fix-sqli-fp123" in result["pr"]["branch"]

    # Check that PR body has Ed25519 signature
    saved_job = store.get("job-e2e-gh")
    assert saved_job.state == JobState.PR_CREATED
    assert saved_job.pr_number == 1
    assert saved_job.verified_sha == "a"*40

    # Ensure Check Runs were updated
    assert len(fake_gh.check_runs) >= 1
    assert any(cr.conclusion == "success" for cr in fake_gh.check_runs)
