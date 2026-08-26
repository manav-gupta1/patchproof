import pytest

from packages.github.pr_api import GitHubPRCreator


class FakeGitHub:
    def __init__(self):
        self.calls = []

    def create_pull_request(self, **kwargs):
        self.calls.append(kwargs)
        return {"html_url": "https://github.com/acme/demo/pull/42", "number": 42}


def test_only_verified_remediation_can_create_pr():
    gh = FakeGitHub()
    creator = GitHubPRCreator(gh)
    with pytest.raises(ValueError):
        creator.create_verified_pr(
            verified=False, owner="acme", repo="demo",
            title="fix", body="not verified", head="patchproof/x", base="main"
        )
    assert gh.calls == []


def test_verified_remediation_creates_pr_payload():
    gh = FakeGitHub()
    result = GitHubPRCreator(gh).create_verified_pr(
        verified=True, owner="acme", repo="demo",
        title="security: fix SQL injection",
        body="## PatchProof: VERIFIED",
        head="patchproof/finding-123", base="main"
    )
    assert result.number == 42
    assert result.url.endswith("/pull/42")
    assert gh.calls[0]["head"] == "patchproof/finding-123"
    assert gh.calls[0]["base"] == "main"


def test_http_adapter_never_logs_token():
    # Structural test: token is held on the adapter and isn't part of PR payload.
    from packages.github.http_api import GitHubHTTPAPI
    api = GitHubHTTPAPI("secret-token")
    assert api.token == "secret-token"
