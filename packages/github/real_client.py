from __future__ import annotations
from dataclasses import dataclass
import json
import urllib.error
import urllib.request


class GitHubAPIError(RuntimeError):
    pass


@dataclass(frozen=True)
class GitHubConfig:
    api_url: str = "https://api.github.com"
    token: str = ""
    owner: str = ""
    repo: str = ""

    def validate(self):
        if not self.token:
            raise GitHubAPIError("GitHub token is required")
        if not self.owner or not self.repo:
            raise GitHubAPIError("GitHub owner/repo is required")


class GitHubAPIClient:
    def __init__(self, config: GitHubConfig):
        config.validate()
        self.config = config

    def _request(self, method, path, payload=None):
        url = self.config.api_url.rstrip("/") + path
        data = None if payload is None else json.dumps(payload).encode()
        req = urllib.request.Request(
            url, data=data, method=method,
            headers={
                "Authorization": f"Bearer {self.config.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                raw = response.read().decode()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise GitHubAPIError(f"GitHub API {exc.code}: {detail[:1000]}") from exc
        except urllib.error.URLError as exc:
            raise GitHubAPIError("GitHub API request failed") from exc

    def find_pull_request(self, *, head, base, evidence_sha256):
        prs = self._request(
            "GET",
            f"/repos/{self.config.owner}/{self.config.repo}/pulls"
            f"?state=open&head={self.config.owner}:{head}&base={base}",
        )
        marker = f"patchproof-evidence:{evidence_sha256}"
        for pr in prs:
            if marker in (pr.get("body") or ""):
                return {
                    "number": pr["number"],
                    "url": pr["html_url"],
                    "head_sha": pr["head"]["sha"],
                }
        return None

    def create_pull_request(self, *, title, body, head, base, evidence_sha256):
        marker = f"patchproof-evidence:{evidence_sha256}"
        final_body = f"{body.rstrip()}\n\n{marker}"
        pr = self._request(
            "POST",
            f"/repos/{self.config.owner}/{self.config.repo}/pulls",
            {"title": title, "body": final_body, "head": head, "base": base},
        )
        return {
            "number": pr["number"],
            "url": pr["html_url"],
            "head_sha": pr["head"]["sha"],
        }
