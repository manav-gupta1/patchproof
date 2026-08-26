from __future__ import annotations

import json
from urllib import error, request


class GitHubHTTPAPI:
    """Minimal GitHub REST adapter; token is supplied by the GitHub App layer."""
    def __init__(self, token: str, *, api_base: str = "https://api.github.com"):
        if not token:
            raise ValueError("GitHub token is required")
        self.token = token
        self.api_base = api_base.rstrip("/")

    def create_pull_request(self, *, owner, repo, title, body, head, base):
        url = f"{self.api_base}/repos/{owner}/{repo}/pulls"
        payload = json.dumps({
            "title": title,
            "body": body,
            "head": head,
            "base": base,
        }).encode()
        req = request.Request(
            url, data=payload, method="POST",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
            },
        )
        try:
            with request.urlopen(req, timeout=30) as response:
                return json.loads(response.read())
        except error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise RuntimeError(
                f"GitHub API PR creation failed ({exc.code}): {detail}"
            ) from exc
