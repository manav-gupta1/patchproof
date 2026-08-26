from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packages.github.auth import sanitize_secret_text
from packages.github.transport import (
    GitHubAPIError,
    GitHubAuthError,
    GitHubConflictError,
    GitHubNotFoundError,
    GitHubPermissionError,
    GitHubRateLimitError,
    GitHubUnprocessableError,
    RequestsGitHubTransport,
)


@dataclass(frozen=True)
class PullRequestRef:
    number: int
    url: str
    head_sha: str | None = None
    branch: str | None = None
    base_branch: str | None = None
    repository: str | None = None

    @property
    def html_url(self) -> str:
        return self.url

    def to_dict(self) -> dict[str, Any]:
        d = {"number": self.number, "url": self.url}
        if self.head_sha:
            d["head_sha"] = self.head_sha
        if self.branch:
            d["branch"] = self.branch
        if self.base_branch:
            d["base_branch"] = self.base_branch
        if self.repository:
            d["repository"] = self.repository
        return d


class GitHubAppClient:
    """Production GitHub client using GitHub App authentication and transport."""

    PROTECTED_BRANCHES = {"main", "master", "develop", "prod", "production", "release"}

    def __init__(self, auth: Any, transport: Any = None) -> None:
        self.auth = auth
        self.transport = transport or RequestsGitHubTransport()

    def get_token(self, installation_id: int | None = None) -> str:
        if self.auth is None:
            raise GitHubAPIError("Authentication provider is required")
        if hasattr(self.auth, "installation_token"):
            return self.auth.installation_token(installation_id or 1).token
        if hasattr(self.auth, "token"):
            return self.auth.token
        raise GitHubAPIError("Invalid authentication provider")

    def _split_repo(self, repository: str) -> tuple[str, str]:
        if "/" not in repository:
            raise GitHubAPIError(f"Invalid repository full name '{repository}', expected 'owner/repo'")
        owner, repo = repository.split("/", 1)
        return owner, repo

    def get_repository(self, repository: str, installation_id: int | None = None) -> dict[str, Any]:
        """Fetch repository details and permissions."""
        owner, repo = self._split_repo(repository)
        token = self.get_token(installation_id)
        if hasattr(self.transport, "get_repository"):
            return self.transport.get_repository(token=token, owner=owner, repo=repo)
        return {"full_name": repository, "default_branch": "main"}

    def verify_repository_permissions(
        self,
        repository: str,
        required_permissions: list[str] | dict[str, bool] | None = None,
        installation_id: int | None = None,
    ) -> bool:
        """Verify that the GitHub App installation has access and permissions for repository."""
        owner, repo = self._split_repo(repository)
        token = self.get_token(installation_id)

        try:
            repo_info = self.get_repository(repository, installation_id=installation_id)
        except GitHubNotFoundError:
            raise GitHubPermissionError(f"Repository {repository} not accessible or not found for installation")
        except GitHubAuthError:
            raise

        perms = repo_info.get("permissions", {})
        if required_permissions and isinstance(perms, dict) and perms:
            if isinstance(required_permissions, list):
                for p in required_permissions:
                    if not perms.get(p, False) and not perms.get("admin", False) and not perms.get("push", False):
                        raise GitHubPermissionError(f"Missing required repository permission '{p}' on {repository}")
            elif isinstance(required_permissions, dict):
                for p, req in required_permissions.items():
                    if req and not perms.get(p, False) and not perms.get("admin", False) and not perms.get("push", False):
                        raise GitHubPermissionError(f"Missing required repository permission '{p}' on {repository}")

        return True

    def get_pull_request(self, repository: str, pr_number: int, installation_id: int | None = None) -> PullRequestRef | None:
        """Get details for an existing Pull Request."""
        owner, repo = self._split_repo(repository)
        token = self.get_token(installation_id)
        if hasattr(self.transport, "get_pull_request"):
            try:
                res = self.transport.get_pull_request(token=token, owner=owner, repo=repo, pr_number=pr_number)
                if res:
                    return PullRequestRef(
                        number=int(res["number"]),
                        url=res.get("html_url") or res.get("url", ""),
                        head_sha=res.get("head", {}).get("sha") if isinstance(res.get("head"), dict) else None,
                        branch=res.get("head", {}).get("ref") if isinstance(res.get("head"), dict) else None,
                        base_branch=res.get("base", {}).get("ref") if isinstance(res.get("base"), dict) else None,
                        repository=repository,
                    )
            except GitHubNotFoundError:
                return None
        return None

    def get_ref(self, repository: str, ref: str, installation_id: int | None = None) -> dict[str, Any] | None:
        """Get git reference SHA from GitHub repository."""
        owner, repo = self._split_repo(repository)
        token = self.get_token(installation_id)
        if hasattr(self.transport, "get_ref"):
            try:
                return self.transport.get_ref(token=token, owner=owner, repo=repo, ref=ref)
            except GitHubNotFoundError:
                return None
        return None

    def create_branch(self, repository: str, branch: str, base_sha: str, installation_id: int | None = None) -> str:
        """Create a new branch ref on remote GitHub repository with collision avoidance."""
        if branch in self.PROTECTED_BRANCHES:
            raise GitHubPermissionError(f"Cannot overwrite protected branch '{branch}'")

        owner, repo = self._split_repo(repository)
        token = self.get_token(installation_id)

        clean_branch = branch.replace("refs/heads/", "")
        ref_path = f"heads/{clean_branch}"

        if hasattr(self.transport, "create_ref"):
            try:
                self.transport.create_ref(token=token, owner=owner, repo=repo, ref=ref_path, sha=base_sha)
                return clean_branch
            except GitHubUnprocessableError:
                existing = self.get_ref(repository, ref_path, installation_id=installation_id)
                if existing:
                    return clean_branch
                raise
        return clean_branch

    def delete_branch(self, repository: str, branch: str, installation_id: int | None = None) -> bool:
        """Delete a branch ref from remote GitHub repository."""
        if branch in self.PROTECTED_BRANCHES:
            raise GitHubPermissionError(f"Cannot delete protected branch '{branch}'")

        owner, repo = self._split_repo(repository)
        token = self.get_token(installation_id)
        if hasattr(self.transport, "delete_ref"):
            return self.transport.delete_ref(token=token, owner=owner, repo=repo, ref=branch)
        return True

    def close_pull_request(self, repository: str, pr_number: int, installation_id: int | None = None) -> PullRequestRef:
        """Close an open pull request."""
        return self.update_pull_request(
            repository=repository,
            pr_number=pr_number,
            state="closed",
            installation_id=installation_id,
        )

    def push_branch(
        self,
        *,
        workspace_path: str | Path,
        repository: str,
        branch: str,
        installation_id: int | None = None,
        remote_name: str = "origin",
    ) -> None:
        """Push a local branch to the remote GitHub repository using installation auth."""
        if branch in self.PROTECTED_BRANCHES:
            raise GitHubPermissionError(f"Cannot overwrite protected branch '{branch}'")

        token = self.get_token(installation_id)
        auth_url = f"https://x-access-token:{token}@github.com/{repository}.git"
        ws = Path(workspace_path)

        try:
            proc = subprocess.run(
                ["git", "push", "--force", auth_url, f"{branch}:{branch}"],
                cwd=ws,
                text=True,
                capture_output=True,
                check=False,
            )
            if proc.returncode != 0:
                sanitized_stderr = proc.stderr.replace(token, "[REDACTED]")
                raise GitHubAPIError(f"Git push failed (exit code {proc.returncode}): {sanitized_stderr.strip()}")
        except GitHubAPIError:
            raise
        except Exception as exc:
            err_str = str(exc).replace(token, "[REDACTED]")
            raise GitHubAPIError(f"Failed to push branch {branch} to GitHub: {err_str}") from None

    def create_pull_request(
        self,
        *,
        installation_id: int | None = None,
        repository: str,
        head: str,
        base: str = "main",
        title: str = "Security remediation",
        body: str = "",
        idempotency_key: str | None = None,
    ) -> PullRequestRef:
        """Create a Pull Request with complete idempotency checks and secret protection."""
        if head in self.PROTECTED_BRANCHES:
            raise GitHubPermissionError(f"Cannot create PR using protected branch '{head}' as head")

        owner, name = self._split_repo(repository)
        token = self.get_token(installation_id)
        marker = idempotency_key or f"patchproof:{head}:{base}"

        # 1. Check if PR already exists by idempotency marker
        if hasattr(self.transport, "find_pull_request_by_marker"):
            try:
                existing = self.transport.find_pull_request_by_marker(
                    token=token,
                    owner=owner,
                    repo=name,
                    marker=marker,
                )
                if existing:
                    return PullRequestRef(
                        number=int(existing["number"]),
                        url=existing.get("html_url") or existing.get("url", ""),
                        head_sha=existing.get("head", {}).get("sha") if isinstance(existing.get("head"), dict) else None,
                        branch=head,
                        base_branch=base,
                        repository=repository,
                    )
            except Exception:
                pass

        # 2. Check if PR already exists for the head branch
        if hasattr(self.transport, "find_pull_request_by_branch"):
            try:
                existing_by_branch = self.transport.find_pull_request_by_branch(
                    token=token,
                    owner=owner,
                    repo=name,
                    head=head,
                    base=base,
                )
                if existing_by_branch:
                    return PullRequestRef(
                        number=int(existing_by_branch["number"]),
                        url=existing_by_branch.get("html_url") or existing_by_branch.get("url", ""),
                        head_sha=existing_by_branch.get("head", {}).get("sha") if isinstance(existing_by_branch.get("head"), dict) else None,
                        branch=head,
                        base_branch=base,
                        repository=repository,
                    )
            except Exception:
                pass

        # 3. Create the PR with the idempotency marker embedded in the body
        final_body = f"{body.rstrip()}\n\n<!-- {marker} -->" if marker not in body else body
        try:
            result = self.transport.create_pull_request(
                token=token,
                owner=owner,
                repo=name,
                head=head,
                base=base,
                title=title,
                body=final_body,
            )
        except Exception as exc:
            # Re-check after failure to handle remote success on timeout or race condition
            if hasattr(self.transport, "find_pull_request_by_marker"):
                try:
                    existing = self.transport.find_pull_request_by_marker(
                        token=token, owner=owner, repo=name, marker=marker
                    )
                    if existing:
                        return PullRequestRef(
                            number=int(existing["number"]),
                            url=existing.get("html_url") or existing.get("url", ""),
                            head_sha=existing.get("head", {}).get("sha") if isinstance(existing.get("head"), dict) else None,
                            branch=head,
                            base_branch=base,
                            repository=repository,
                        )
                except Exception:
                    pass
            if hasattr(self.transport, "find_pull_request_by_branch"):
                try:
                    existing_by_branch = self.transport.find_pull_request_by_branch(
                        token=token, owner=owner, repo=name, head=head, base=base
                    )
                    if existing_by_branch:
                        return PullRequestRef(
                            number=int(existing_by_branch["number"]),
                            url=existing_by_branch.get("html_url") or existing_by_branch.get("url", ""),
                            head_sha=existing_by_branch.get("head", {}).get("sha") if isinstance(existing_by_branch.get("head"), dict) else None,
                            branch=head,
                            base_branch=base,
                            repository=repository,
                        )
                except Exception:
                    pass

            sanitized = str(exc).replace(token, "[REDACTED]")
            raise GitHubAPIError(f"GitHub PR creation failed: {sanitized}") from exc

        return PullRequestRef(
            number=int(result["number"]),
            url=result.get("html_url") or result.get("url", ""),
            head_sha=result.get("head", {}).get("sha") if isinstance(result.get("head"), dict) else None,
            branch=head,
            base_branch=base,
            repository=repository,
        )

    def update_pull_request(
        self,
        *,
        installation_id: int | None = None,
        repository: str,
        pr_number: int,
        title: str | None = None,
        body: str | None = None,
        state: str | None = None,
    ) -> PullRequestRef:
        """Update an existing Pull Request."""
        owner, name = self._split_repo(repository)
        token = self.get_token(installation_id)

        if hasattr(self.transport, "update_pull_request"):
            result = self.transport.update_pull_request(
                token=token,
                owner=owner,
                repo=name,
                pr_number=pr_number,
                title=title,
                body=body,
                state=state,
            )
            return PullRequestRef(
                number=int(result.get("number", pr_number)),
                url=result.get("html_url") or result.get("url", ""),
                head_sha=result.get("head", {}).get("sha") if isinstance(result.get("head"), dict) else None,
                branch=result.get("head", {}).get("ref") if isinstance(result.get("head"), dict) else None,
                base_branch=result.get("base", {}).get("ref") if isinstance(result.get("base"), dict) else None,
                repository=repository,
            )
        return PullRequestRef(number=pr_number, url=f"https://github.com/{repository}/pull/{pr_number}", repository=repository)

    def get_commit(self, repository: str, commit_sha: str, installation_id: int | None = None) -> dict[str, Any]:
        """Fetch details for a specific commit SHA."""
        owner, repo = self._split_repo(repository)
        token = self.get_token(installation_id)
        if hasattr(self.transport, "get_commit"):
            return self.transport.get_commit(token=token, owner=owner, repo=repo, commit_sha=commit_sha)
        return {"sha": commit_sha, "commit": {"message": ""}}

    def list_commits(self, repository: str, branch: str | None = None, installation_id: int | None = None) -> list[dict[str, Any]]:
        """List commits in repository."""
        owner, repo = self._split_repo(repository)
        token = self.get_token(installation_id)
        if hasattr(self.transport, "list_commits"):
            return self.transport.list_commits(token=token, owner=owner, repo=repo, branch=branch)
        return []

    def create_check_run(
        self,
        *,
        repository: str,
        head_sha: str,
        name: str = "PatchProof Security Remediation",
        status: str = "queued",
        conclusion: str | None = None,
        completed_at: str | None = None,
        installation_id: int | None = None,
        external_id: str | None = None,
        output: dict[str, Any] | None = None,
    ) -> Any:
        from packages.github.check_runs import CheckRunRef

        owner, repo = self._split_repo(repository)
        token = self.get_token(installation_id)

        try:
            result = self.transport.create_check_run(
                token=token,
                owner=owner,
                repo=repo,
                name=name,
                head_sha=head_sha,
                status=status,
                conclusion=conclusion,
                completed_at=completed_at,
                external_id=external_id,
                output=output,
            )
            return CheckRunRef(
                id=int(result["id"]),
                name=result.get("name", name),
                head_sha=result.get("head_sha", head_sha),
                status=result.get("status", status),
                conclusion=result.get("conclusion", conclusion),
                html_url=result.get("html_url"),
                url=result.get("url"),
                details_url=result.get("details_url"),
            )
        except Exception as exc:
            sanitized = str(exc).replace(token, "[REDACTED]")
            raise GitHubAPIError(f"Failed to create GitHub Check Run: {sanitized}") from exc

    def update_check_run(
        self,
        *,
        repository: str,
        check_run_id: int,
        status: str | None = None,
        conclusion: str | None = None,
        completed_at: str | None = None,
        installation_id: int | None = None,
        output: dict[str, Any] | None = None,
    ) -> Any:
        from packages.github.check_runs import CheckRunRef

        owner, repo = self._split_repo(repository)
        token = self.get_token(installation_id)

        try:
            result = self.transport.update_check_run(
                token=token,
                owner=owner,
                repo=repo,
                check_run_id=check_run_id,
                status=status,
                conclusion=conclusion,
                completed_at=completed_at,
                output=output,
            )
            return CheckRunRef(
                id=int(result.get("id", check_run_id)),
                name=result.get("name", "PatchProof Security Remediation"),
                head_sha=result.get("head_sha", ""),
                status=result.get("status", status or "completed"),
                conclusion=result.get("conclusion", conclusion),
                html_url=result.get("html_url"),
                url=result.get("url"),
                details_url=result.get("details_url"),
            )
        except Exception as exc:
            sanitized = str(exc).replace(token, "[REDACTED]")
            raise GitHubAPIError(f"Failed to update GitHub Check Run {check_run_id}: {sanitized}") from exc
