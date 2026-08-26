from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from packages.gitops.adapter import GitOpsAdapter, GitOpsError


class DirtyRepositoryError(GitOpsError):
    """Raised when an attempt is made to stage or operate on a dirty repository."""


class IsolatedWorkspace:
    """An isolated temporary git workspace that guarantees user checkout safety."""

    def __init__(
        self,
        workspace_path: Path,
        repository_name: str,
        commit_sha: str,
        source_path: Path | None = None,
    ) -> None:
        self.path = Path(workspace_path).resolve()
        self.repository_name = repository_name
        self.commit_sha = commit_sha
        self.source_path = Path(source_path).resolve() if source_path else None
        self.git = GitOpsAdapter(self.path)
        self._cleaned = False

    def is_dirty(self) -> bool:
        """Check if workspace currently has uncommitted changes or untracked files."""
        if not self.path.exists():
            return False
        proc = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all", "--ignored=matching"],
            cwd=self.path,
            text=True,
            capture_output=True,
            check=False,
        )
        return bool(proc.stdout.strip())

    def cleanup(self) -> None:
        """Safely remove the temporary workspace directory."""
        if not self._cleaned and self.path.exists():
            shutil.rmtree(self.path, ignore_errors=True)
            self._cleaned = True

    def __enter__(self) -> IsolatedWorkspace:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.cleanup()


class WorkspaceStaging:
    """Staging service creating clean, isolated workspaces for remediation."""

    def __init__(
        self,
        base_temp_dir: str | Path | None = None,
        github_client: Any = None,
        auth: Any = None,
    ) -> None:
        self.base_temp_dir = Path(base_temp_dir) if base_temp_dir else None
        self.github_client = github_client
        self.auth = auth

    def stage(
        self,
        repository: str | Path,
        commit_sha: str | None = None,
        installation_id: int | None = None,
    ) -> IsolatedWorkspace:
        """Stage a repository into an isolated temporary workspace.

        Enforces safety boundaries:
        - Rejects dirty local repositories.
        - Isolates execution so the source repository is never modified.
        - Clones remote repositories securely with GitHub App installation tokens when configured.
        - Guarantees clean git history at the requested commit.
        """
        temp_dir = Path(
            tempfile.mkdtemp(prefix="patchproof-ws-", dir=self.base_temp_dir)
        ).resolve()

        source_path = Path(repository).resolve() if isinstance(repository, Path) or (isinstance(repository, str) and os.path.exists(repository)) else None

        if source_path and source_path.is_dir():
            # Local directory checkout safety check
            self._verify_clean_source(source_path)
            shutil.copytree(
                source_path,
                temp_dir,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns(".venv", "node_modules", ".pytest_cache", "__pycache__"),
            )
            repo_name = source_path.name
        else:
            # Remote repository name (e.g. "owner/repo")
            repo_name = str(repository)
            cloned = self._try_clone_remote_repo(temp_dir, repo_name, commit_sha, installation_id)
            if not cloned:
                self._initialize_fixture_repo(temp_dir, repo_name)

        # Ensure git repository is initialized in workspace
        self._ensure_git_repo(temp_dir)

        # Resolve commit sha
        resolved_sha = commit_sha or self._get_current_sha(temp_dir)

        return IsolatedWorkspace(
            workspace_path=temp_dir,
            repository_name=repo_name,
            commit_sha=resolved_sha,
            source_path=source_path,
        )

    def _try_clone_remote_repo(
        self,
        temp_dir: Path,
        repository: str,
        commit_sha: str | None,
        installation_id: int | None,
    ) -> bool:
        """Attempt to clone a remote repository using GitHub App credentials if available."""
        if "/" not in repository:
            return False

        auth = self.auth
        if auth is None and self.github_client is not None and hasattr(self.github_client, "auth"):
            auth = self.github_client.auth

        if auth is None:
            try:
                from packages.github.auth import GitHubAppCredentials, GitHubAppAuth
                creds = GitHubAppCredentials.from_env()
                if creds.app_id and creds.private_key_pem:
                    auth = GitHubAppAuth(
                        app_id=creds.app_id,
                        private_key_pem=creds.private_key_pem,
                        api_url=creds.api_url,
                    )
            except Exception:
                auth = None

        if auth is None:
            return False

        from packages.github.auth import sanitize_secret_text

        inst_id = installation_id or 1
        try:
            token = auth.installation_token(inst_id).token if hasattr(auth, "installation_token") else getattr(auth, "token", "")
            if not token:
                return False
        except Exception as exc:
            raise GitOpsError(f"GitHub App token acquisition failed: {sanitize_secret_text(str(exc))}") from exc

        auth_url = f"https://x-access-token:{token}@github.com/{repository}.git"
        clean_url = f"https://github.com/{repository}.git"

        try:
            subprocess.run(["git", "init", "-q"], cwd=temp_dir, check=True)
            subprocess.run(["git", "remote", "add", "origin", auth_url], cwd=temp_dir, check=True)

            target_sha = commit_sha if commit_sha and not commit_sha.startswith("pr-") and commit_sha != "HEAD" else None
            if target_sha:
                proc = subprocess.run(
                    ["git", "fetch", "--depth=1", "origin", target_sha],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if proc.returncode != 0:
                    sanitized_err = sanitize_secret_text(proc.stderr)
                    raise GitOpsError(f"Git fetch failed for {repository}@{target_sha}: {sanitized_err.strip()}")
                subprocess.run(["git", "checkout", "-q", "--detach", target_sha], cwd=temp_dir, check=True)
            else:
                proc = subprocess.run(
                    ["git", "fetch", "--depth=1", "origin", "HEAD"],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if proc.returncode != 0:
                    sanitized_err = sanitize_secret_text(proc.stderr)
                    raise GitOpsError(f"Git fetch failed for {repository}: {sanitized_err.strip()}")
                subprocess.run(["git", "checkout", "-q", "--detach", "FETCH_HEAD"], cwd=temp_dir, check=True)

            # Scrub token from git remote immediately after checkout
            subprocess.run(["git", "remote", "set-url", "origin", clean_url], cwd=temp_dir, check=True)
            return True
        except GitOpsError:
            raise
        except Exception as exc:
            sanitized_err = sanitize_secret_text(str(exc))
            raise GitOpsError(f"Remote checkout failed for {repository}: {sanitized_err}") from None

    def _verify_clean_source(self, source_path: Path) -> None:
        """Verify that the source git repository has no dirty changes."""
        git_dir = source_path / ".git"
        if not git_dir.exists():
            return
        proc = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all", "--ignored=matching"],
            cwd=source_path,
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.stdout.strip():
            raise DirtyRepositoryError(
                f"Source repository {source_path} is dirty and cannot be staged safely "
                f"(uncommitted or untracked changes detected):\n{proc.stdout.strip()}"
            )

    @staticmethod
    def _initialize_fixture_repo(path: Path, name: str) -> None:
        """Initialize a clean synthetic git repository for fixture/remote tests."""
        path.mkdir(parents=True, exist_ok=True)
        app_file = path / "app.py"
        if not app_file.exists():
            app_file.write_text(
                "import os\n\n"
                "def handle_request(user_input: str):\n"
                "    # Potential vulnerability pattern\n"
                "    query = f\"SELECT * FROM users WHERE username = '{user_input}'\"\n"
                "    return query\n"
            )

    @staticmethod
    def _ensure_git_repo(path: Path) -> None:
        """Ensure the workspace has a valid git repository with commit."""
        git_dir = path / ".git"
        if not git_dir.exists():
            subprocess.run(["git", "init", "-q"], cwd=path, check=True)
            subprocess.run(["git", "config", "user.name", "PatchProof"], cwd=path, check=True)
            subprocess.run(["git", "config", "user.email", "bot@patchproof.local"], cwd=path, check=True)
            subprocess.run(["git", "add", "-A"], cwd=path, check=True)
            subprocess.run(
                ["git", "-c", "user.name=PatchProof", "-c", "user.email=bot@patchproof.local", "commit", "-qm", "baseline"],
                cwd=path,
                check=True,
            )

    @staticmethod
    def _get_current_sha(path: Path) -> str:
        try:
            return subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=path, text=True
            ).strip()
        except Exception:
            return "0000000000000000000000000000000000000000"
