from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class RepoCheckout:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()

    def validate_relative_path(self, path: str) -> Path:
        candidate = (self.root / path).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise ValueError("path escapes repository root")
        return candidate

    def read_file(self, path: str) -> str:
        target = self.validate_relative_path(path)
        if not target.is_file():
            raise FileNotFoundError(path)
        return target.read_text(errors="replace")

    def git(self, *args: str) -> str:
        proc = subprocess.run(
            ["git", "-C", str(self.root), *args],
            text=True,
            capture_output=True,
            check=True,
        )
        return proc.stdout

    def changed_files(self) -> list[str]:
        output = self.git("diff", "--name-only")
        return [line for line in output.splitlines() if line.strip()]
