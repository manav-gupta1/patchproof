import time
import pytest

from packages.github.auth import GitHubAppAuth, GitHubAuthError
from packages.github.client import GitHubAppClient, GitHubAPIError


class AuthTransport:
    def create_app_jwt(self, **kwargs):
        return "jwt"

    def create_installation_token(self, **kwargs):
        return {"token": "inst-token", "expires_at": int(time.time()) + 3600}


def test_installation_token():
    auth = GitHubAppAuth("123", "pem", AuthTransport())
    token = auth.installation_token(42)
    assert token.token == "inst-token"
    assert not token.expired


def test_missing_token_rejected():
    class Bad:
        def create_app_jwt(self, **kwargs): return "jwt"
        def create_installation_token(self, **kwargs): return {}
    with pytest.raises(GitHubAuthError):
        GitHubAppAuth("1", "pem", Bad()).installation_token(2)


class Transport:
    def __init__(self):
        self.created = 0
        self.existing = None
        self.fail_once = False

    def create_pull_request(self, **kwargs):
        self.created += 1
        if self.fail_once:
            self.fail_once = False
            self.existing = {"number": 9, "html_url": "https://github.test/pr/9", "body": "marker-1"}
            raise RuntimeError("timeout after remote creation")
        return {"number": 8, "html_url": "https://github.test/pr/8"}

    def find_pull_request_by_marker(self, **kwargs):
        return self.existing


class Auth:
    def installation_token(self, installation_id):
        return type("T", (), {"token": "token"})()


def test_pr_idempotency_reuses_existing():
    transport = Transport()
    transport.existing = {"number": 7, "html_url": "https://github.test/pr/7"}
    client = GitHubAppClient(Auth(), transport)
    pr = client.create_pull_request(
        installation_id=1, repository="acme/repo", head="b", base="main",
        title="fix", body="marker-1", idempotency_key="marker-1"
    )
    assert pr.number == 7
    assert transport.created == 0


def test_pr_timeout_rechecks_and_avoids_duplicate():
    transport = Transport()
    transport.fail_once = True
    client = GitHubAppClient(Auth(), transport)
    pr = client.create_pull_request(
        installation_id=1, repository="acme/repo", head="b", base="main",
        title="fix", body="marker-1", idempotency_key="marker-1"
    )
    assert pr.number == 9
    assert transport.created == 1


def test_unresolved_github_failure_is_error():
    transport = Transport()
    transport.fail_once = True
    transport.create_pull_request = lambda **kwargs: (_ for _ in ()).throw(RuntimeError("boom"))
    client = GitHubAppClient(Auth(), transport)
    with pytest.raises(GitHubAPIError):
        client.create_pull_request(
            installation_id=1, repository="acme/repo", head="b", base="main",
            title="fix", body="marker-1", idempotency_key="marker-1"
        )
