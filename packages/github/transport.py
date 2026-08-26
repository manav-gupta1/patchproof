from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class GitHubAPIError(RuntimeError):
    """Base error raised when GitHub API requests return an error."""


class GitHubAuthError(GitHubAPIError):
    """Raised when GitHub App authentication or token acquisition fails (HTTP 401)."""


class GitHubPermissionError(GitHubAPIError):
    """Raised when GitHub App lacks necessary permissions for repository (HTTP 403)."""


class GitHubNotFoundError(GitHubAPIError):
    """Raised when requested GitHub repository, PR, or reference is not found (HTTP 404)."""


class GitHubConflictError(GitHubAPIError):
    """Raised on branch ref or merge conflicts (HTTP 409)."""


class GitHubUnprocessableError(GitHubAPIError):
    """Raised when request payload is unprocessable, e.g. PR already exists (HTTP 422)."""


class GitHubRateLimitError(GitHubAPIError):
    """Raised when GitHub secondary or primary rate limits are exceeded (HTTP 429)."""

    def __init__(self, message: str, retry_after: int = 60) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class GitHubServerError(GitHubAPIError):
    """Raised when GitHub API returns 5xx server errors."""


class GitHubTransientError(GitHubServerError):
    """Raised when GitHub API encounters transient server or timeout errors."""


# Semantic aliases for structured error model
GitHubAuthenticationError = GitHubAuthError
GitHubAuthorizationError = GitHubPermissionError


class RequestsGitHubTransport:
    """HTTP transport for GitHub API with session or standard urllib backend."""

    API = "https://api.github.com"

    def __init__(self, session: Any = None, api_url: str = "https://api.github.com") -> None:
        self.session = session
        self.api_url = api_url.rstrip("/")

    def create_app_jwt(self, *, app_id: str, private_key_pem: str) -> str:
        # JWT creation is managed in the auth layer.
        raise NotImplementedError("JWT creation is handled by GitHubAppAuth")

    def _http_request(
        self,
        method: str,
        path: str,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        retries: int = 2,
    ) -> Any:
        url = f"{self.api_url}/{path.lstrip('/')}"
        if params:
            query = urllib.parse.urlencode(params)
            url = f"{url}?{query}"

        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "PatchProof-Remediation-Platform",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if data is not None:
            headers["Content-Type"] = "application/json"

        attempts = 0
        while True:
            attempts += 1
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=20) as resp:
                    body = resp.read().decode("utf-8")
                    return json.loads(body) if body else {}
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode(errors="replace")
                status = exc.code

                if status == 401:
                    raise GitHubAuthError(f"GitHub API authentication failed (401 Unauthorized): {detail[:200]}") from exc
                elif status == 403:
                    # Check for rate limit
                    if "rate limit" in detail.lower():
                        retry_after = int(exc.headers.get("Retry-After", "60"))
                        raise GitHubRateLimitError(f"GitHub API rate limited (403): {detail[:200]}", retry_after=retry_after) from exc
                    raise GitHubPermissionError(f"GitHub API permission denied (403 Forbidden): {detail[:200]}") from exc
                elif status == 404:
                    raise GitHubNotFoundError(f"GitHub resource not found (404 Not Found): {detail[:200]}") from exc
                elif status == 409:
                    raise GitHubConflictError(f"GitHub conflict (409 Conflict): {detail[:200]}") from exc
                elif status == 422:
                    raise GitHubUnprocessableError(f"GitHub unprocessable entity (422): {detail[:200]}") from exc
                elif status == 429:
                    retry_after = int(exc.headers.get("Retry-After", "60"))
                    if attempts <= retries and method in ("GET", "HEAD"):
                        time.sleep(min(retry_after, 2))
                        continue
                    raise GitHubRateLimitError(f"GitHub API rate limit exceeded (429): {detail[:200]}", retry_after=retry_after) from exc
                elif status >= 500:
                    if attempts <= retries and method in ("GET", "HEAD"):
                        time.sleep(0.5 * attempts)
                        continue
                    raise GitHubServerError(f"GitHub API server error {status}: {detail[:200]}") from exc
                else:
                    raise GitHubAPIError(f"GitHub API error {status}: {detail[:200]}") from exc
            except urllib.error.URLError as exc:
                if attempts <= retries and method in ("GET", "HEAD"):
                    time.sleep(0.5 * attempts)
                    continue
                raise GitHubAPIError(f"GitHub API network failure: {exc.reason}") from exc

    def create_installation_token(self, *, jwt: str, installation_id: int) -> dict[str, Any]:
        if self.session is not None:
            response = self.session.post(
                f"{self.api_url}/app/installations/{installation_id}/access_tokens",
                headers={
                    "Authorization": f"Bearer {jwt}",
                    "Accept": "application/vnd.github+json",
                },
                timeout=15,
            )
            response.raise_for_status()
            return response.json()

        return self._http_request(
            method="POST",
            path=f"/app/installations/{installation_id}/access_tokens",
            token=jwt,
            payload={},
        )

    def get_repository(self, *, token: str, owner: str, repo: str) -> dict[str, Any]:
        if self.session is not None:
            response = self.session.get(
                f"{self.api_url}/repos/{owner}/{repo}",
                headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
                timeout=15,
            )
            response.raise_for_status()
            return response.json()

        return self._http_request(
            method="GET",
            path=f"/repos/{owner}/{repo}",
            token=token,
        )

    def get_pull_request(self, *, token: str, owner: str, repo: str, pr_number: int) -> dict[str, Any]:
        if self.session is not None:
            response = self.session.get(
                f"{self.api_url}/repos/{owner}/{repo}/pulls/{pr_number}",
                headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
                timeout=15,
            )
            response.raise_for_status()
            return response.json()

        return self._http_request(
            method="GET",
            path=f"/repos/{owner}/{repo}/pulls/{pr_number}",
            token=token,
        )

    def get_ref(self, *, token: str, owner: str, repo: str, ref: str) -> dict[str, Any]:
        clean_ref = ref.lstrip("refs/")
        if self.session is not None:
            response = self.session.get(
                f"{self.api_url}/repos/{owner}/{repo}/git/ref/{clean_ref}",
                headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
                timeout=15,
            )
            response.raise_for_status()
            return response.json()

        return self._http_request(
            method="GET",
            path=f"/repos/{owner}/{repo}/git/ref/{clean_ref}",
            token=token,
        )

    def create_ref(self, *, token: str, owner: str, repo: str, ref: str, sha: str) -> dict[str, Any]:
        ref_name = f"refs/{ref}" if not ref.startswith("refs/") else ref
        if self.session is not None:
            response = self.session.post(
                f"{self.api_url}/repos/{owner}/{repo}/git/refs",
                json={"ref": ref_name, "sha": sha},
                headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
                timeout=15,
            )
            response.raise_for_status()
            return response.json()

        return self._http_request(
            method="POST",
            path=f"/repos/{owner}/{repo}/git/refs",
            token=token,
            payload={"ref": ref_name, "sha": sha},
        )

    def update_ref(self, *, token: str, owner: str, repo: str, ref: str, sha: str, force: bool = False) -> dict[str, Any]:
        clean_ref = ref.lstrip("refs/")
        if self.session is not None:
            response = self.session.patch(
                f"{self.api_url}/repos/{owner}/{repo}/git/refs/{clean_ref}",
                json={"sha": sha, "force": force},
                headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
                timeout=15,
            )
            response.raise_for_status()
            return response.json()

        return self._http_request(
            method="PATCH",
            path=f"/repos/{owner}/{repo}/git/refs/{clean_ref}",
            token=token,
            payload={"sha": sha, "force": force},
        )

    def delete_ref(self, *, token: str, owner: str, repo: str, ref: str) -> bool:
        clean_ref = ref.replace("refs/", "").replace("heads/", "")
        if self.session is not None:
            response = self.session.delete(
                f"{self.api_url}/repos/{owner}/{repo}/git/refs/heads/{clean_ref}",
                headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
                timeout=15,
            )
            return response.status_code in (204, 404)

        try:
            self._http_request(
                method="DELETE",
                path=f"/repos/{owner}/{repo}/git/refs/heads/{clean_ref}",
                token=token,
            )
            return True
        except GitHubNotFoundError:
            return True

    def get_commit(self, *, token: str, owner: str, repo: str, commit_sha: str) -> dict[str, Any]:
        if self.session is not None:
            response = self.session.get(
                f"{self.api_url}/repos/{owner}/{repo}/commits/{commit_sha}",
                headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
                timeout=15,
            )
            response.raise_for_status()
            return response.json()

        return self._http_request(
            method="GET",
            path=f"/repos/{owner}/{repo}/commits/{commit_sha}",
            token=token,
        )

    def list_commits(self, *, token: str, owner: str, repo: str, branch: str | None = None) -> list[dict[str, Any]]:
        params = {"sha": branch} if branch else None
        if self.session is not None:
            response = self.session.get(
                f"{self.api_url}/repos/{owner}/{repo}/commits",
                params=params,
                headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
                timeout=15,
            )
            response.raise_for_status()
            return response.json()

        return self._http_request(
            method="GET",
            path=f"/repos/{owner}/{repo}/commits",
            token=token,
            params=params,
        )

    def find_pull_request_by_marker(
        self,
        *,
        token: str,
        owner: str,
        repo: str,
        marker: str,
    ) -> dict[str, Any] | None:
        if self.session is not None:
            response = self.session.get(
                f"{self.api_url}/repos/{owner}/{repo}/pulls",
                params={"state": "open", "per_page": 100},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                },
                timeout=15,
            )
            response.raise_for_status()
            for pr in response.json():
                if marker in (pr.get("body") or ""):
                    return pr
            return None

        prs = self._http_request(
            method="GET",
            path=f"/repos/{owner}/{repo}/pulls",
            token=token,
            params={"state": "open", "per_page": 100},
        )
        if isinstance(prs, list):
            for pr in prs:
                if marker in (pr.get("body") or ""):
                    return pr
        return None

    def find_pull_request_by_branch(
        self,
        *,
        token: str,
        owner: str,
        repo: str,
        head: str,
        base: str,
    ) -> dict[str, Any] | None:
        head_query = f"{owner}:{head}" if ":" not in head else head
        prs = self._http_request(
            method="GET",
            path=f"/repos/{owner}/{repo}/pulls",
            token=token,
            params={"state": "open", "head": head_query, "base": base},
        )
        if isinstance(prs, list) and prs:
            return prs[0]
        return None

    def create_pull_request(
        self,
        *,
        token: str,
        owner: str,
        repo: str,
        head: str,
        base: str,
        title: str,
        body: str,
    ) -> dict[str, Any]:
        if self.session is not None:
            response = self.session.post(
                f"{self.api_url}/repos/{owner}/{repo}/pulls",
                json={"head": head, "base": base, "title": title, "body": body},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                },
                timeout=20,
            )
            response.raise_for_status()
            return response.json()

        return self._http_request(
            method="POST",
            path=f"/repos/{owner}/{repo}/pulls",
            token=token,
            payload={"head": head, "base": base, "title": title, "body": body},
        )

    def update_pull_request(
        self,
        *,
        token: str,
        owner: str,
        repo: str,
        pr_number: int,
        title: str | None = None,
        body: str | None = None,
        state: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if title is not None:
            payload["title"] = title
        if body is not None:
            payload["body"] = body
        if state is not None:
            payload["state"] = state

        if self.session is not None:
            response = self.session.patch(
                f"{self.api_url}/repos/{owner}/{repo}/pulls/{pr_number}",
                json=payload,
                headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
                timeout=15,
            )
            response.raise_for_status()
            return response.json()

        return self._http_request(
            method="PATCH",
            path=f"/repos/{owner}/{repo}/pulls/{pr_number}",
            token=token,
            payload=payload,
        )

    def create_check_run(
        self,
        *,
        token: str,
        owner: str,
        repo: str,
        name: str,
        head_sha: str,
        status: str = "queued",
        conclusion: str | None = None,
        completed_at: str | None = None,
        external_id: str | None = None,
        output: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": name,
            "head_sha": head_sha,
            "status": status,
        }
        if conclusion is not None:
            payload["conclusion"] = conclusion
        if completed_at is not None:
            payload["completed_at"] = completed_at
        if external_id:
            payload["external_id"] = external_id
        if output:
            payload["output"] = output

        if self.session is not None:
            response = self.session.post(
                f"{self.api_url}/repos/{owner}/{repo}/check-runs",
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                },
                timeout=20,
            )
            response.raise_for_status()
            return response.json()

        return self._http_request(
            method="POST",
            path=f"/repos/{owner}/{repo}/check-runs",
            token=token,
            payload=payload,
        )

    def update_check_run(
        self,
        *,
        token: str,
        owner: str,
        repo: str,
        check_run_id: int,
        status: str | None = None,
        conclusion: str | None = None,
        completed_at: str | None = None,
        output: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if status is not None:
            payload["status"] = status
        if conclusion is not None:
            payload["conclusion"] = conclusion
        if completed_at is not None:
            payload["completed_at"] = completed_at
        if output is not None:
            payload["output"] = output

        if self.session is not None:
            response = self.session.patch(
                f"{self.api_url}/repos/{owner}/{repo}/check-runs/{check_run_id}",
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                },
                timeout=20,
            )
            response.raise_for_status()
            return response.json()

        return self._http_request(
            method="PATCH",
            path=f"/repos/{owner}/{repo}/check-runs/{check_run_id}",
            token=token,
            payload=payload,
        )
