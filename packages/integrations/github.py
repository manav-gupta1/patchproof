from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from urllib.request import Request, urlopen


class GitHubError(RuntimeError):
    pass


def verify_signature(secret: str, body: bytes, signature: str) -> bool:
    if not signature.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@dataclass
class GitHubFinding:
    repository: str
    commit_sha: str
    fingerprint: str
    rule_id: str
    path: str
    start_line: int
    end_line: int
    severity: str


class GitHubClient:
    def __init__(self, token: str, api_base: str = "https://api.github.com") -> None:
        self.token = token
        self.api_base = api_base.rstrip("/")

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        body = None if payload is None else json.dumps(payload).encode()
        req = Request(
            self.api_base + path,
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(req, timeout=30) as response:
                return json.load(response)
        except Exception as exc:
            raise GitHubError(f"GitHub request failed: {exc}") from exc

    def create_branch(self, repository: str, branch: str, sha: str) -> dict:
        return self._request(
            "POST",
            f"/repos/{repository}/git/refs",
            {"ref": f"refs/heads/{branch}", "sha": sha},
        )

    def create_pull_request(
        self, repository: str, title: str, head: str, base: str, body: str
    ) -> dict:
        return self._request(
            "POST",
            f"/repos/{repository}/pulls",
            {"title": title, "head": head, "base": base, "body": body},
        )

    def post_comment(self, repository: str, issue_number: int, body: str) -> dict:
        return self._request(
            "POST",
            f"/repos/{repository}/issues/{issue_number}/comments",
            {"body": body},
        )


def parse_code_scanning_alert(payload: dict) -> GitHubFinding:
    alert = payload.get("alert", payload)
    repo = payload.get("repository", {}).get("full_name", "unknown/unknown")
    instance = alert.get("most_recent_instance") or payload.get("most_recent_instance") or {}
    location = instance.get("location", {})
    return GitHubFinding(
        repository=repo,
        commit_sha=instance.get("commit_sha") or payload.get("commit_sha", ""),
        fingerprint=(instance.get("fingerprint") or alert.get("fingerprint") or payload.get("fingerprint", "")),
        rule_id=alert.get("rule", {}).get("id", alert.get("rule_id", "")),
        path=location.get("path", ""),
        start_line=int(location.get("start_line", 1)),
        end_line=int(location.get("end_line", location.get("start_line", 1))),
        severity=alert.get("severity", "unknown"),
    )
