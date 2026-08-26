from __future__ import annotations

import json
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
    GitHubAuthenticationError,
    GitHubAuthorizationError,
    GitHubConflictError,
    GitHubNotFoundError,
    GitHubPermissionError,
    GitHubRateLimitError,
    GitHubServerError,
    GitHubTransientError,
    GitHubUnprocessableError,
    RequestsGitHubTransport,
)
from packages.github.publisher import GitHubPublisher, PublicationRejected
from packages.jobs.state import JobRecord, JobState, JobStateMachine
from packages.jobs.store import InMemoryJobStore
from packages.jobs.orchestrator import RemediationOrchestrator
from packages.jobs.pipeline_factory import (
    ConcreteGitHubPublisher,
    create_concrete_remediation_orchestrator,
)
from packages.signing import Ed25519EvidenceSigner


@pytest.fixture
def rsa_key_pair():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return {"private_pem": private_pem, "public_pem": public_pem, "public_key": key.public_key()}


# ==============================================================================
# 1. GitHub App Configuration & Modes Tests
# ==============================================================================

def test_production_mode_missing_credentials_raises_auth_error(monkeypatch):
    monkeypatch.setenv("PATCHPROOF_ENVIRONMENT", "production")
    monkeypatch.delenv("GITHUB_APP_ID", raising=False)
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY_PATH", raising=False)

    store = InMemoryJobStore()
    publisher = ConcreteGitHubPublisher()

    job = JobRecord(
        job_id="job-prod-missing-creds",
        repository="acme/secure-repo",
        delivery_id="deliv-prod-1",
        state=JobState.VERIFIED,
    )
    store.create(job)

    patch_result = {
        "title": "fix: security patch",
        "branch": "patchproof/remediation/job-prod-missing-creds",
        "base_branch": "main",
        "diff": "--- a\n+++ b",
    }
    evidence = {"verified": True, "commit_sha": job.commit_sha}

    with pytest.raises(GitHubAuthError, match="Production mode requires"):
        publisher.publish_verified(job=job, patch_result=patch_result, evidence=evidence)


def test_development_mode_graceful_fallback(monkeypatch):
    monkeypatch.setenv("PATCHPROOF_ENVIRONMENT", "development")
    monkeypatch.delenv("GITHUB_APP_ID", raising=False)
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY", raising=False)

    store = InMemoryJobStore()
    publisher = ConcreteGitHubPublisher()

    job = JobRecord(
        job_id="job-dev-fallback",
        repository="acme/dev-repo",
        delivery_id="deliv-dev-1",
        state=JobState.VERIFIED,
    )
    store.create(job)

    patch_result = {
        "title": "fix: dev patch",
        "branch": "patchproof/remediation/job-dev-fallback",
        "base_branch": "main",
        "diff": "--- a\n+++ b",
    }
    evidence = {"verified": True, "commit_sha": job.commit_sha}

    result = publisher.publish_verified(job=job, patch_result=patch_result, evidence=evidence)
    assert result["number"] == 1
    assert "https://github.com/acme/dev-repo/pull/1" in result["url"]


# ==============================================================================
# 2. JWT Generation & Secret Redaction Tests
# ==============================================================================

def test_jwt_rs256_claims_and_clock_skew(rsa_key_pair):
    app_id = "554433"
    token = create_app_jwt(app_id=app_id, private_key_pem=rsa_key_pair["private_pem"])

    # Verify signature and payload
    decoded = jwt.decode(token, rsa_key_pair["public_key"], algorithms=["RS256"])
    assert decoded["iss"] == "554433"
    assert decoded["exp"] > decoded["iat"]
    # Issued at is 60s in the past for clock-skew safety
    now = int(time.time())
    assert decoded["iat"] <= now
    assert decoded["exp"] <= now + 660


def test_secret_redaction_in_diagnostics(rsa_key_pair):
    pem = rsa_key_pair["private_pem"]
    token = "ghs_1234567890abcdef1234567890abcdef1234"
    text_with_secrets = (
        f"Failed to authenticate with key {pem} and token {token} on URL https://x-access-token:{token}@github.com/org/repo.git"
    )
    sanitized = sanitize_secret_text(text_with_secrets)
    assert pem not in sanitized
    assert token not in sanitized
    assert "[REDACTED_PRIVATE_KEY]" in sanitized
    assert "[REDACTED_TOKEN]" in sanitized
    assert "[REDACTED_AUTH]" in sanitized


# ==============================================================================
# 3. Installation Token Caching & Thread Safety Tests
# ==============================================================================

def test_installation_token_caching_and_expiration(rsa_key_pair):
    call_counts = {"token_requests": 0}

    class MockGitHubApi:
        def create_app_jwt(self, **kwargs):
            return "mock-jwt-token"

        def create_installation_token(self, jwt, installation_id):
            call_counts["token_requests"] += 1
            # Return token expiring in 1 hour
            return {
                "token": f"ghs_token_{call_counts['token_requests']}",
                "expires_at": int(time.time()) + 3600,
            }

    auth = GitHubAppAuth(
        app_id="123",
        private_key_pem=rsa_key_pair["private_pem"],
        github_client=MockGitHubApi(),
    )

    # First call: fetches new token
    t1 = auth.installation_token(installation_id=42)
    assert t1.token == "ghs_token_1"
    assert call_counts["token_requests"] == 1

    # Second call (immediate): uses cached token
    t2 = auth.installation_token(installation_id=42)
    assert t2.token == "ghs_token_1"
    assert call_counts["token_requests"] == 1


def test_concurrent_token_acquisition_thread_safety(rsa_key_pair):
    call_counts = {"count": 0}

    class MockGitHubApi:
        def create_app_jwt(self, **kwargs):
            return "mock-jwt-token"

        def create_installation_token(self, jwt, installation_id):
            time.sleep(0.01)
            call_counts["count"] += 1
            return {
                "token": "ghs_thread_safe_token",
                "expires_at": int(time.time()) + 3600,
            }

    auth = GitHubAppAuth(
        app_id="123",
        private_key_pem=rsa_key_pair["private_pem"],
        github_client=MockGitHubApi(),
    )

    results = []

    def worker():
        tok = auth.installation_token(installation_id=99)
        results.append(tok.token)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 10
    assert all(r == "ghs_thread_safe_token" for r in results)
    assert call_counts["count"] == 1  # Exactly one token acquisition due to thread lock


# ==============================================================================
# 4. Repository Authorization & Permission Verification Tests
# ==============================================================================

def test_repository_authorization_allowed(rsa_key_pair):
    class MockTransport:
        def get_repository(self, token, owner, repo):
            return {
                "full_name": f"{owner}/{repo}",
                "permissions": {"push": True, "pull": True, "admin": False},
                "default_branch": "main",
            }

    auth = GitHubAppAuth(
        app_id="123",
        private_key_pem=rsa_key_pair["private_pem"],
        github_client=type("C", (), {"create_app_jwt": lambda *a, **k: "jwt", "create_installation_token": lambda *a, **k: {"token": "t", "expires_at": int(time.time()) + 3600}})(),
    )
    client = GitHubAppClient(auth=auth, transport=MockTransport())

    assert client.verify_repository_permissions("octocat/Hello-World", required_permissions=["push"]) is True


def test_repository_authorization_unauthorized_fails_closed(rsa_key_pair):
    class MockTransport:
        def get_repository(self, token, owner, repo):
            raise GitHubNotFoundError("Repository not found or installation lacks access")

    auth = GitHubAppAuth(
        app_id="123",
        private_key_pem=rsa_key_pair["private_pem"],
        github_client=type("C", (), {"create_app_jwt": lambda *a, **k: "jwt", "create_installation_token": lambda *a, **k: {"token": "t", "expires_at": int(time.time()) + 3600}})(),
    )
    client = GitHubAppClient(auth=auth, transport=MockTransport())

    with pytest.raises(GitHubPermissionError, match="not accessible"):
        client.verify_repository_permissions("unauthorized-org/private-repo")


# ==============================================================================
# 5. Rate Limiting & Error Model Tests
# ==============================================================================

def test_rate_limit_error_mapping_and_semantic_aliases():
    err = GitHubRateLimitError("API rate limit exceeded", retry_after=120)
    assert isinstance(err, GitHubAPIError)
    assert err.retry_after == 120

    # Test semantic aliases
    assert issubclass(GitHubAuthenticationError, GitHubAPIError)
    assert issubclass(GitHubAuthorizationError, GitHubAPIError)
    assert issubclass(GitHubTransientError, GitHubAPIError)


# ==============================================================================
# 6. Idempotent PR Creation & Safety Gate Invariant Tests
# ==============================================================================

def test_safety_invariant_unverified_job_blocks_github_writes(rsa_key_pair):
    write_calls = {"branch_created": 0, "pr_created": 0}

    class MockTransport:
        def create_ref(self, *a, **k):
            write_calls["branch_created"] += 1

        def create_pull_request(self, *a, **k):
            write_calls["pr_created"] += 1
            return {"number": 1, "url": "https://github.com/org/repo/pull/1"}

    auth = GitHubAppAuth(
        app_id="123",
        private_key_pem=rsa_key_pair["private_pem"],
        github_client=type("C", (), {"create_app_jwt": lambda *a, **k: "jwt", "create_installation_token": lambda *a, **k: {"token": "t", "expires_at": int(time.time()) + 3600}})(),
    )
    client = GitHubAppClient(auth=auth, transport=MockTransport())

    publisher = GitHubPublisher(client=client)
    job = JobRecord(
        job_id="job-unverified-test",
        repository="org/repo",
        delivery_id="deliv-unverif",
        commit_sha="a" * 40,
        state=JobState.VERIFYING,  # NOT verified!
    )

    # Attempt publication without VERIFIED state or valid evidence
    with pytest.raises(PublicationRejected):
        publisher.publish_verified(
            job=job,
            patch_result=type("P", (), {"diff": "diff", "branch": "patchproof/fix", "base_branch": "main", "title": "fix"})(),
            evidence=type("E", (), {"verified": False, "commit_sha": job.commit_sha, "patch_sha256": "fake"})(),
        )

    # Absolute zero GitHub writes
    assert write_calls["branch_created"] == 0
    assert write_calls["pr_created"] == 0


def test_idempotent_pr_creation_finds_existing_marker(rsa_key_pair):
    create_calls = {"count": 0}

    class MockTransport:
        def find_pull_request_by_marker(self, token, owner, repo, marker):
            if "patchproof:job-idempotent-001" in marker:
                return {
                    "number": 88,
                    "url": f"https://github.com/{owner}/{repo}/pull/88",
                    "head": {"sha": "c" * 40},
                }
            return None

        def create_pull_request(self, *a, **k):
            create_calls["count"] += 1
            return {"number": 99, "url": "new-pr"}

    auth = GitHubAppAuth(
        app_id="123",
        private_key_pem=rsa_key_pair["private_pem"],
        github_client=type("C", (), {"create_app_jwt": lambda *a, **k: "jwt", "create_installation_token": lambda *a, **k: {"token": "t", "expires_at": int(time.time()) + 3600}})(),
    )
    client = GitHubAppClient(auth=auth, transport=MockTransport())

    pr = client.create_pull_request(
        repository="octocat/Hello-World",
        head="patchproof/fix",
        base="main",
        idempotency_key="patchproof:job-idempotent-001",
    )

    # Reused existing PR #88 without calling create_pull_request
    assert pr.number == 88
    assert pr.url == "https://github.com/octocat/Hello-World/pull/88"
    assert create_calls["count"] == 0


# ==============================================================================
# 7. End-to-End Orchestrated Pipeline with Production GitHub App Flow
# ==============================================================================

def test_e2e_production_github_app_pipeline(rsa_key_pair):
    store = InMemoryJobStore()
    created_prs = []

    class FakeProductionGitHubTransport:
        def __init__(self):
            self.prs = {}

        def get_repository(self, token, owner, repo):
            return {
                "full_name": f"{owner}/{repo}",
                "permissions": {"push": True, "pull": True},
                "default_branch": "main",
            }

        def create_ref(self, token, owner, repo, ref, sha):
            return {"ref": ref, "object": {"sha": sha}}

        def get_ref(self, token, owner, repo, ref):
            return None

        def find_pull_request_by_marker(self, token, owner, repo, marker):
            return None

        def find_pull_request_by_branch(self, token, owner, repo, head, base):
            return None

        def create_pull_request(self, token, owner, repo, head, base, title, body):
            pr_num = len(self.prs) + 101
            res = {
                "number": pr_num,
                "html_url": f"https://github.com/{owner}/{repo}/pull/{pr_num}",
                "head": {"sha": "9" * 40, "ref": head},
                "base": {"ref": base},
            }
            self.prs[pr_num] = res
            created_prs.append(res)
            return res

        def create_check_run(self, token, owner, repo, name, head_sha, status, **kwargs):
            return {"id": 555, "name": name, "status": status, "head_sha": head_sha}

        def update_check_run(self, token, owner, repo, check_run_id, status, **kwargs):
            return {"id": check_run_id, "name": "PatchProof", "status": status}

    transport = FakeProductionGitHubTransport()
    auth = GitHubAppAuth(
        app_id="998811",
        private_key_pem=rsa_key_pair["private_pem"],
        github_client=type("C", (), {
            "create_app_jwt": lambda *a, **k: "jwt-prod-token",
            "create_installation_token": lambda *a, **k: {"token": "ghs_prod_token", "expires_at": int(time.time()) + 3600},
        })(),
    )
    github_client = GitHubAppClient(auth=auth, transport=transport)
    publisher = ConcreteGitHubPublisher(client=github_client, installation_id=1)
    signer = Ed25519EvidenceSigner()

    job = JobRecord(
        job_id="job-prod-e2e-001",
        repository="enterprise/production-service",
        delivery_id="deliv-prod-e2e-1",
        commit_sha="9" * 40,
        target_branch="main",
        installation_id=1,
    )
    store.create(job)

    class MockVerification:
        verified = True
        findings = []

    orchestrator = RemediationOrchestrator(
        store=store,
        state_machine=JobStateMachine(),
        clone=lambda repo, sha: "/tmp/fake-workspace",
        scan=lambda ws: [{"rule_id": "rule-sqli", "severity": "HIGH", "fingerprint": "fp-e2e"}],
        analyze=lambda ws, f: {"candidate": None, "finding": f[0], "context": None},
        patch=lambda ws, p: {
            "applied_files": ["app.py"],
            "diff": "--- a/app.py\n+++ b/app.py",
            "rule_id": "rule-sqli",
            "title": "fix(security): sanitize sql input",
            "explanation": "Replaced raw format string with parameterized database query.",
            "head_branch": "patchproof/remediation/job-prod-e2e-001",
            "base_branch": "main",
        },
        verify=lambda **kwargs: MockVerification(),
        evidence=lambda *args, **kwargs: signer.sign({
            "job_id": job.job_id,
            "repository": job.repository,
            "commit_sha": job.commit_sha,
            "verified": True,
            "evidence_id": "ev-e2e-prod-1",
            "target_finding": {"rule_id": "rule-sqli", "severity": "HIGH"},
        }),
        github=publisher,
    )

    # Execute full pipeline run
    result = orchestrator.run("job-prod-e2e-001")

    # 1. State machine reached PR_CREATED in store
    job_record = store.get("job-prod-e2e-001")
    state_val = getattr(job_record.state, "value", job_record.state)
    assert state_val == "pr_created"

    # 2. PR created on GitHub
    assert len(created_prs) == 1
    assert created_prs[0]["number"] == 101

    # 3. Store has PR recorded and evidence signed
    stored_pr = store.get_pr("job-prod-e2e-001")
    assert stored_pr["number"] == 101
    assert "https://github.com/enterprise/production-service/pull/101" in stored_pr["url"]

    evidence = store.get_evidence("job-prod-e2e-001")
    assert evidence is not None
    assert evidence["verified"] is True
    assert evidence["signature"] is not None

    # 4. Events recorded in order
    events = store.get_events("job-prod-e2e-001")
    state_sequence = [e["to_state"] for e in events]
    assert "queued" in state_sequence
    assert "scanning" in state_sequence
    assert "analyzing" in state_sequence
    assert "patching" in state_sequence
    assert "verifying" in state_sequence
    assert "verified" in state_sequence
    assert "pr_created" in state_sequence
