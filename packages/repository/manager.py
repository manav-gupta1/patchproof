from __future__ import annotations

import subprocess
from pathlib import Path


class RepositoryError(RuntimeError):
    pass


class RepositoryManager:
    """Small, deterministic Git checkout abstraction for local and worker use."""

    def checkout(self, repository_url: str, commit_sha: str, destination: str | Path) -> Path:
        destination = Path(destination).resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() and any(destination.iterdir()):
            raise RepositoryError(f"Checkout destination is not empty: {destination}")

        self._run(["git", "clone", "--no-checkout", "--depth", "1", repository_url, str(destination)])
        self._run(["git", "-C", str(destination), "fetch", "--depth", "1", "origin", commit_sha])
        self._run(["git", "-C", str(destination), "checkout", "--detach", commit_sha])
        return destination

    @staticmethod
    def _run(command: list[str]) -> None:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RepositoryError(result.stderr.strip() or "Git command failed")
