from packages.github.real_client import GitHubAPIClient, GitHubConfig, GitHubAPIError


def test_github_config_fails_closed():
    try:
        GitHubAPIClient(GitHubConfig())
        assert False
    except GitHubAPIError:
        assert True


def test_github_client_marks_evidence(monkeypatch):
    client = GitHubAPIClient(GitHubConfig(token="secret", owner="o", repo="r"))
    calls = []

    def fake(method, path, payload=None):
        calls.append((method, path, payload))
        return {"number": 7, "html_url": "u", "head": {"sha": "abc"}}

    monkeypatch.setattr(client, "_request", fake)
    result = client.create_pull_request(
        title="x", body="body", head="patchproof/x",
        base="main", evidence_sha256="deadbeef"
    )
    assert result["number"] == 7
    assert "patchproof-evidence:deadbeef" in calls[0][2]["body"]


def test_find_uses_evidence_marker(monkeypatch):
    client = GitHubAPIClient(GitHubConfig(token="secret", owner="o", repo="r"))
    monkeypatch.setattr(client, "_request", lambda *a, **k: [{
        "number": 3, "html_url": "u", "head": {"sha": "sha"},
        "body": "patchproof-evidence:abc"
    }])
    assert client.find_pull_request(
        head="patchproof/x", base="main", evidence_sha256="abc"
    )["number"] == 3
