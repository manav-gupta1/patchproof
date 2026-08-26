from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import subprocess
import tempfile


@dataclass(frozen=True)
class HarnessResult:
    passed: bool
    stages: tuple[str, ...]
    output: str = ""


class ControlledRepository:
    """Creates a disposable local Git repository for end-to-end pipeline tests."""

    def __init__(self, source: str):
        self.source = source

    def create(self):
        path = Path(tempfile.mkdtemp(prefix="patchproof-e2e-"))
        (path / "app.py").write_text(self.source)
        subprocess.run(["git", "init", "-q"], cwd=path, check=True)
        subprocess.run(["git", "add", "."], cwd=path, check=True)
        subprocess.run(
            ["git", "-c", "user.name=PatchProof", "-c",
             "user.email=test@patchproof.local", "commit", "-qm", "baseline"],
            cwd=path, check=True,
        )
        sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=path, text=True
        ).strip()
        return path, sha


def run_controlled_smoke(orchestrator, job_id):
    result = orchestrator.run(job_id)
    return HarnessResult(
        passed=result["state"] == "pr_created",
        stages=("job", "scan", "analyze", "patch", "verify", "pr"),
        output=str(result),
    )
