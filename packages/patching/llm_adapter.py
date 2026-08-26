from __future__ import annotations
import subprocess
from pathlib import Path


class SafePatchApplier:
    def apply(self, repository: Path, proposal):
        changed = set(proposal.changed_files)
        if not changed:
            raise ValueError("empty patch")

        for path in changed:
            p = Path(path)
            if p.is_absolute() or ".." in p.parts:
                raise ValueError(f"unsafe patch path: {path}")

        before = subprocess.run(
            ["git", "diff", "--check"], cwd=repository,
            capture_output=True, text=True
        )
        if before.returncode:
            raise ValueError("repository already has whitespace errors")

        applied = subprocess.run(
            ["git", "apply", "--check", "--whitespace=error"],
            cwd=repository, input=proposal.diff,
            capture_output=True, text=True
        )
        if applied.returncode:
            raise ValueError(f"patch rejected: {applied.stderr}")

        applied = subprocess.run(
            ["git", "apply", "--whitespace=error"],
            cwd=repository, input=proposal.diff,
            capture_output=True, text=True
        )
        if applied.returncode:
            raise RuntimeError(f"patch application failed: {applied.stderr}")

        diff_files = subprocess.run(
            ["git", "diff", "--name-only"], cwd=repository,
            capture_output=True, text=True, check=True
        ).stdout.splitlines()
        unexpected = set(diff_files) - changed
        if unexpected:
            raise ValueError(f"patch changed undeclared files: {sorted(unexpected)}")

        return tuple(diff_files)
