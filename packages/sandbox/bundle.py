from __future__ import annotations
from pathlib import Path
import os
import shutil
import tempfile


class BundleError(RuntimeError):
    pass


class WorkspaceBundle:
    def __init__(self, source: Path):
        self.source = source.resolve()
        self.path = None

    def __enter__(self):
        if not self.source.is_dir():
            raise BundleError("repository source is not a directory")
        self.path = Path(tempfile.mkdtemp(prefix="patchproof-sandbox-"))
        target = self.path / "repo"
        shutil.copytree(
            self.source,
            target,
            symlinks=False,
            ignore=shutil.ignore_patterns(
                ".git", "__pycache__", ".pytest_cache", ".venv", "node_modules"
            ),
        )
        # The worker owns the temporary bundle; repository changes cannot escape
        # into the original checkout.
        return target

    def __exit__(self, exc_type, exc, tb):
        if self.path and self.path.exists():
            shutil.rmtree(self.path, ignore_errors=True)
        return False
