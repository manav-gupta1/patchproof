from __future__ import annotations

import os
import time
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from packages.github.auth import GitHubAppAuth, GitHubAppCredentials, GitHubAuthError
from packages.github.client import GitHubAppClient, PullRequestRef
from packages.github.diagnostics import get_github_config_diagnostics, print_github_config_diagnostics
from packages.github.integration_runner import (
    ControlledGitHubIntegrationRunner,
    ControlledIntegrationAudit,
    ControlledIntegrationError,
)
from packages.github.transport import RequestsGitHubTransport


@pytest.fixture
def rsa_key_pair():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    return {"private_pem": private_pem, "public_key": key.public_key()}


# ==============================================================================
# 1. Safe Diagnostics Tests
# ==============================================================================

def test_diagnostics_safe_output(monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_APP_ID", "12345")
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", "-----BEGIN RSA PRIVATE KEY-----\nMY_PRIVATE_KEY_MATERIAL\n-----END RSA PRIVATE KEY-----")
    monkeypatch.delenv("PATCHPROOF_TEST_REPOSITORY", raising=False)

    diag = get_github_config_diagnostics()
    assert diag["GITHUB_APP_ID"] == "configured: yes"
    assert diag["GITHUB_APP_PRIVATE_KEY"] == "configured: yes"
    assert diag["PATCHPROOF_TEST_REPOSITORY"] == "configured: no"

    # Verify print output contains NO secret values
    print_github_config_diagnostics()
    captured = capsys.readouterr().out
    assert "configured: yes" in captured
    assert "MY_PRIVATE_KEY_MATERIAL" not in captured
    assert "-----BEGIN" not in captured


# ==============================================================================
# 2. Integration Mode Guard & Configuration Tests
# ==============================================================================

def test_integration_mode_disabled_by_default(monkeypatch):
    monkeypatch.delenv("PATCHPROOF_GITHUB_INTEGRATION_TEST", raising=False)
    with pytest.raises(ControlledIntegrationError, match="Controlled real GitHub integration is not enabled"):
        ControlledGitHubIntegrationRunner.from_env()


def test_integration_mode_missing_test_repo_fails(monkeypatch, rsa_key_pair):
    monkeypatch.setenv("PATCHPROOF_GITHUB_INTEGRATION_TEST", "true")
    monkeypatch.delenv("PATCHPROOF_TEST_REPOSITORY", raising=False)
    monkeypatch.setenv("GITHUB_APP_ID", "123")
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", rsa_key_pair["private_pem"])

    with pytest.raises(ControlledIntegrationError, match="Missing or invalid PATCHPROOF_TEST_REPOSITORY"):
        ControlledGitHubIntegrationRunner.from_env()


def test_repository_substitution_rejected(rsa_key_pair):
    auth = GitHubAppAuth(app_id="123", private_key_pem=rsa_key_pair["private_pem"], github_client=type("C", (), {"create_app_jwt": lambda *a, **k: "jwt", "create_installation_token": lambda *a, **k: {"token": "t", "expires_at": int(time.time())+3600}})())
    client = GitHubAppClient(auth=auth)

    runner = ControlledGitHubIntegrationRunner(
        auth=auth,
        client=client,
        test_repository="acme/allowed-test-repo",
    )

    # Allowed test repo passes
    runner.validate_target_repository("acme/allowed-test-repo")

    # Substitution attempt fails closed
    with pytest.raises(ControlledIntegrationError, match="Refusing operation on repository 'production/core-repo'"):
        runner.validate_target_repository("production/core-repo")


def test_protected_branch_rejection(rsa_key_pair):
    auth = GitHubAppAuth(app_id="123", private_key_pem=rsa_key_pair["private_pem"], github_client=type("C", (), {"create_app_jwt": lambda *a, **k: "jwt", "create_installation_token": lambda *a, **k: {"token": "t", "expires_at": int(time.time())+3600}})())
    client = GitHubAppClient(auth=auth)

    runner = ControlledGitHubIntegrationRunner(
        auth=auth,
        client=client,
        test_repository="acme/allowed-test-repo",
    )

    for protected in ["main", "master", "production", "develop", "release"]:
        assert protected in runner.PROTECTED_BRANCHES


# ==============================================================================
# 3. Negative Safety Path Test (Mandatory Verification Failure Gate)
# ==============================================================================

def test_negative_safety_test_blocks_github_writes(rsa_key_pair):
    write_calls = {"branch_created": 0, "pr_created": 0}

    class MockTransport:
        def create_ref(self, *a, **k):
            write_calls["branch_created"] += 1

        def create_pull_request(self, *a, **k):
            write_calls["pr_created"] += 1
            return {"number": 1, "url": "https://github.com/test/repo/pull/1"}

    auth = GitHubAppAuth(app_id="123", private_key_pem=rsa_key_pair["private_pem"], github_client=type("C", (), {"create_app_jwt": lambda *a, **k: "jwt", "create_installation_token": lambda *a, **k: {"token": "t", "expires_at": int(time.time())+3600}})())
    client = GitHubAppClient(auth=auth, transport=MockTransport())

    runner = ControlledGitHubIntegrationRunner(
        auth=auth,
        client=client,
        test_repository="acme/test-sandbox",
    )

    # Must pass negative safety check
    assert runner.execute_negative_safety_test() is True
    # Zero GitHub writes
    assert write_calls["branch_created"] == 0
    assert write_calls["pr_created"] == 0


# ==============================================================================
# 4. Controlled Real GitHub Flow with Transport Simulation
# ==============================================================================

def test_controlled_flow_lifecycle_idempotency_and_cleanup(rsa_key_pair):
    call_log = []

    class ControlledMockTransport:
        def __init__(self):
            self.prs = {}
            self.branches = {}

        def get_repository(self, token, owner, repo):
            call_log.append(f"GET_REPO:{owner}/{repo}")
            return {"full_name": f"{owner}/{repo}", "permissions": {"push": True, "pull": True}, "default_branch": "main"}

        def get_ref(self, token, owner, repo, ref):
            return {"object": {"sha": "c0ffee" * 6}}

        def create_ref(self, token, owner, repo, ref, sha):
            call_log.append(f"CREATE_BRANCH:{ref}")
            self.branches[ref] = sha
            return {"ref": ref, "object": {"sha": sha}}

        def find_pull_request_by_marker(self, token, owner, repo, marker):
            for pr in self.prs.values():
                if marker in pr.get("body", ""):
                    call_log.append(f"FIND_PR_BY_MARKER:{pr['number']}")
                    return pr
            return None

        def find_pull_request_by_branch(self, token, owner, repo, head, base):
            return None

        def create_pull_request(self, token, owner, repo, head, base, title, body):
            pr_number = len(self.prs) + 1
            call_log.append(f"CREATE_PR:#{pr_number}")
            pr_data = {
                "number": pr_number,
                "html_url": f"https://github.com/{owner}/{repo}/pull/{pr_number}",
                "head": {"sha": "c0ffee" * 6, "ref": head},
                "base": {"ref": base},
                "body": body,
            }
            self.prs[pr_number] = pr_data
            return pr_data

        def update_pull_request(self, token, owner, repo, pr_number, **kwargs):
            if kwargs.get("state") == "closed":
                call_log.append(f"CLOSE_PR:#{pr_number}")
            return {"number": pr_number, "state": kwargs.get("state", "closed")}

        def delete_ref(self, token, owner, repo, ref):
            call_log.append(f"DELETE_BRANCH:{ref}")
            self.branches.pop(ref, None)
            return True

    transport = ControlledMockTransport()
    auth = GitHubAppAuth(
        app_id="999",
        private_key_pem=rsa_key_pair["private_pem"],
        github_client=type("C", (), {
            "create_app_jwt": lambda *a, **k: "jwt-test",
            "create_installation_token": lambda *a, **k: {"token": "ghs_tok", "expires_at": int(time.time())+3600},
        })(),
    )
    client = GitHubAppClient(auth=auth, transport=transport)

    runner = ControlledGitHubIntegrationRunner(
        auth=auth,
        client=client,
        test_repository="acme/integration-test-repo",
    )

    audit = runner.run_full_controlled_flow(cleanup=True)

    # 1. Verify audit status
    assert audit.authentication == "PASS"
    assert audit.installation_authorization == "PASS"
    assert audit.repository_access == "PASS"
    assert audit.branch_creation == "PASS"
    assert audit.pr_creation == "PASS"
    assert audit.idempotency == "PASS"
    assert audit.negative_safety_path == "PASS"
    assert audit.cleanup == "PASS"

    # 2. Verify sequence of executed actions in call log
    actions = [entry.split(":")[0] for entry in call_log]
    assert "GET_REPO" in actions
    assert "CREATE_BRANCH" in actions
    assert "CREATE_PR" in actions
    assert "FIND_PR_BY_MARKER" in actions  # Idempotency check found existing PR
    assert "CLOSE_PR" in actions           # Cleanup closed PR
    assert "DELETE_BRANCH" in actions      # Cleanup deleted branch

    # 3. Verify audit trail format
    summary = audit.format_summary()
    assert "GitHub App authentication: PASS" in summary
    assert "Negative safety path: PASS" in summary
    assert "Cleanup: PASS" in summary


# ==============================================================================
# 5. Live GitHub Integration Test (Skipped when credentials not in env)
# ==============================================================================

@pytest.mark.skipif(
    os.environ.get("PATCHPROOF_GITHUB_INTEGRATION_TEST", "").lower() not in ("true", "1", "yes")
    or not os.environ.get("PATCHPROOF_TEST_REPOSITORY"),
    reason="Real GitHub credentials and PATCHPROOF_GITHUB_INTEGRATION_TEST=true required for live remote testing",
)
def test_live_real_github_integration():
    """Executes controlled real GitHub integration against live repository when configured."""
    runner = ControlledGitHubIntegrationRunner.from_env()
    audit = runner.run_full_controlled_flow(cleanup=True)
    print(audit.format_summary())
    assert audit.pr_creation == "PASS"
    assert audit.cleanup == "PASS"
