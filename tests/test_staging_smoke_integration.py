from __future__ import annotations

import os
import time
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from fastapi.testclient import TestClient

from packages.api.app import create_app
from packages.auth import ApiKeyStore, TenantContext
from packages.config.guard import validate_production_configuration
from packages.github.auth import GitHubAppAuth
from packages.github.client import GitHubAppClient
from packages.github.diagnostics import get_github_config_diagnostics
from packages.github.installation import InstallationRegistry
from packages.github.integration_runner import ControlledGitHubIntegrationRunner
from packages.jobs.store import InMemoryJobStore
from packages.webhooks.github import GitHubEvent
from packages.webhooks.handlers import WebhookDispatcher


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
# 1. Staging Configuration & Fail-Closed Checks
# ==============================================================================

def test_staging_diagnostics_safe():
    diag = get_github_config_diagnostics()
    # Must report boolean status strings without leaking secret values
    for k, v in diag.items():
        assert v in ("configured: yes", "configured: no")


def test_staging_cors_configuration(monkeypatch):
    monkeypatch.setenv("PATCHPROOF_CORS_ORIGINS", "https://staging.patchproof.io, https://app.patchproof.io")
    store = InMemoryJobStore()
    dispatcher = WebhookDispatcher(jobs=store, enqueue=lambda j: None)
    app = create_app(dispatcher=dispatcher, store=store, webhook_secret="staging-secret", auth_enabled=False)
    client = TestClient(app)

    # Allowed origin receives CORS headers
    resp = client.get("/healthz", headers={"Origin": "https://staging.patchproof.io"})
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "https://staging.patchproof.io"


# ==============================================================================
# 2. Simulated Staging End-to-End Flow & Invariants
# ==============================================================================

def test_staging_simulated_e2e_lifecycle(rsa_key_pair):
    call_log = []

    class StagingMockTransport:
        def __init__(self):
            self.branches = {}
            self.prs = {}

        def get_repository(self, token, owner, repo):
            return {"full_name": f"{owner}/{repo}", "permissions": {"push": True, "pull": True}, "default_branch": "main"}

        def get_ref(self, token, owner, repo, ref):
            return {"object": {"sha": "1234567890abcdef" * 2}}

        def create_ref(self, token, owner, repo, ref, sha):
            call_log.append(f"CREATE_BRANCH:{ref}")
            self.branches[ref] = sha
            return {"ref": ref, "object": {"sha": sha}}

        def create_pull_request(self, token, owner, repo, head, base, title, body):
            pr_num = len(self.prs) + 1
            call_log.append(f"CREATE_PR:#{pr_num}")
            pr_data = {
                "number": pr_num,
                "html_url": f"https://github.com/{owner}/{repo}/pull/{pr_num}",
                "head": {"sha": "1234567890abcdef" * 2, "ref": head},
                "base": {"ref": base},
                "body": body,
            }
            self.prs[pr_num] = pr_data
            return pr_data

        def find_pull_request_by_marker(self, token, owner, repo, marker):
            for pr in self.prs.values():
                if marker in pr.get("body", ""):
                    return pr
            return None

        def find_pull_request_by_branch(self, *a, **k):
            return None

        def update_pull_request(self, token, owner, repo, pr_number, **kwargs):
            call_log.append(f"CLOSE_PR:#{pr_number}")
            return {"number": pr_number, "state": "closed"}

        def delete_ref(self, token, owner, repo, ref):
            call_log.append(f"DELETE_BRANCH:{ref}")
            self.branches.pop(ref, None)
            return True

    auth = GitHubAppAuth(
        app_id="1001",
        private_key_pem=rsa_key_pair["private_pem"],
        github_client=type("C", (), {
            "create_app_jwt": lambda *a, **k: "jwt-staging",
            "create_installation_token": lambda *a, **k: {"token": "ghs_stag", "expires_at": int(time.time())+3600},
        })(),
    )
    client = GitHubAppClient(auth=auth, transport=StagingMockTransport())
    runner = ControlledGitHubIntegrationRunner(
        auth=auth,
        client=client,
        test_repository="patchproof-staging/test-repo",
    )

    audit = runner.run_full_controlled_flow(cleanup=True)
    assert audit.authentication == "PASS"
    assert audit.branch_creation == "PASS"
    assert audit.pr_creation == "PASS"
    assert audit.negative_safety_path == "PASS"
    assert audit.cleanup == "PASS"


# ==============================================================================
# 3. Live Staging Smoke Test (Skipped when credentials are not configured)
# ==============================================================================

@pytest.mark.skipif(
    os.environ.get("PATCHPROOF_GITHUB_INTEGRATION_TEST", "").lower() not in ("true", "1", "yes")
    or not os.environ.get("PATCHPROOF_TEST_REPOSITORY")
    or not os.environ.get("GITHUB_APP_ID")
    or not (os.environ.get("GITHUB_APP_PRIVATE_KEY") or os.environ.get("GITHUB_APP_PRIVATE_KEY_PATH")),
    reason="Live GitHub staging test skipped: requires PATCHPROOF_GITHUB_INTEGRATION_TEST=true and full GitHub App credentials in env",
)
def test_live_staging_remote_github_smoke():
    """Executes live remote GitHub integration test when real staging credentials are provided."""
    runner = ControlledGitHubIntegrationRunner.from_env()
    audit = runner.run_full_controlled_flow(cleanup=True)
    assert audit.pr_creation == "PASS"
    assert audit.cleanup == "PASS"
