from __future__ import annotations

import subprocess
from pathlib import Path

from packages.github.models import CheckoutRequest


class CheckoutError(RuntimeError):
    pass


class GitCheckout:
    """Minimal git checkout adapter.

    The production worker should run this inside a disposable workspace with
    credentials scoped to the single repository and commit.
    """

    def checkout(self, request: CheckoutRequest, clone_url: str) -> str:
        workspace = Path(request.workspace).resolve()
        if workspace.exists() and any(workspace.iterdir()):
            raise CheckoutError("workspace must be empty")

        workspace.mkdir(parents=True, exist_ok=True)

        def run(*args: str) -> None:
            proc = subprocess.run(
                list(args),
                cwd=workspace,
                capture_output=True,
                text=True,
            )
            if proc.returncode:
                raise CheckoutError(proc.stderr[-4000:])

        run("git", "init", "-q")
        run("git", "remote", "add", "origin", clone_url)
        run("git", "fetch", "--depth=1", "origin", request.commit_sha)
        run("git", "checkout", "--detach", request.commit_sha)
        return str(workspace)
