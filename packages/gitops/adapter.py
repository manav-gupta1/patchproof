from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GitOpsResult:
    verified: bool
    branch: str
    commit_sha: str | None
    pushed: bool
    command_log: list[list[str]]


class GitOpsError(RuntimeError):
    pass


class GitOpsAdapter:
    """
    Local Git adapter for the verified-patch promotion boundary.

    This adapter intentionally never performs network operations itself unless
    push=True is explicitly supplied. Production GitHub credentials/token
    handling belongs in the GitHub App adapter.
    """

    def __init__(self, repo: Path):
        self.repo = Path(repo).resolve()
        self.commands: list[list[str]] = []

    def _run(self, *args: str) -> str:
        argv = ["git", *args]
        self.commands.append(argv)
        proc = subprocess.run(
            argv, cwd=self.repo, text=True,
            capture_output=True, check=False,
        )
        if proc.returncode:
            raise GitOpsError(
                f"git command failed: {' '.join(argv)}\n{proc.stderr.strip()}"
            )
        return proc.stdout.strip()

    def prepare_verified_patch(
        self,
        *,
        verified: bool,
        finding_id: str,
        base_sha: str,
        patch_file: Path,
        push: bool = False,
        remote: str = "origin",
    ) -> GitOpsResult:
        if not verified:
            raise GitOpsError("unverified patches cannot enter GitOps promotion")
        if not finding_id:
            raise ValueError("finding_id is required")

        # Explicitly include untracked files; repository-level Git config may
        # otherwise hide them (e.g. status.showUntrackedFiles=no).
        dirty = self._run("status", "--porcelain=v1", "--untracked-files=all", "--ignored=matching")
        if dirty:
            raise GitOpsError("repository must be clean before promotion")

        self._run("checkout", "--detach", base_sha)
        branch = f"patchproof/{finding_id}"
        self._run("switch", "-C", branch)
        self._run("apply", "--check", str(Path(patch_file).resolve()))
        self._run("apply", str(Path(patch_file).resolve()))

        # No promotion without whitespace/error validation.
        self._run("diff", "--check")
        self._run("diff", "--exit-code", "--", ".") if False else None

        self._run("add", "-A")
        status = self._run("status", "--porcelain=v1", "--untracked-files=all", "--ignored=matching")
        if not status:
            raise GitOpsError("patch produced no changes")

        self._run(
            "-c", "user.name=PatchProof",
            "-c", "user.email=bot@patchproof.local",
            "commit", "-m", f"security: remediate {finding_id}",
        )
        commit_sha = self._run("rev-parse", "HEAD")

        pushed = False
        if push:
            self._run("push", "--set-upstream", remote, branch)
            pushed = True

        return GitOpsResult(
            verified=True,
            branch=branch,
            commit_sha=commit_sha,
            pushed=pushed,
            command_log=list(self.commands),
        )
