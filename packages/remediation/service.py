from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import subprocess
import tempfile
import shutil

from packages.context.extractor import ContextExtractor
from packages.ai.patch_generator import PatchGenerator
from packages.patching.llm_adapter import SafePatchApplier


@dataclass(frozen=True)
class RemediationResult:
    status: str
    attempts: int
    changed_files: tuple[str, ...]
    explanation: str
    error: str | None = None


class RemediationService:
    """
    AI proposes; repository tooling applies; verification decides.
    This service deliberately does not mark a patch VERIFIED.
    """

    def __init__(self, model, verifier, max_attempts=2):
        self.generator = PatchGenerator(model)
        self.verifier = verifier
        self.max_attempts = max_attempts

    def remediate(self, repository: Path, finding: dict) -> RemediationResult:
        errors = []
        for attempt in range(1, self.max_attempts + 1):
            try:
                context = ContextExtractor(repository).extract(finding)
                proposal = self.generator.generate(finding, context)
                changed = SafePatchApplier().apply(repository, proposal)

                # The verifier is the authority. Its result is returned to the
                # caller; this layer never converts a model response into VERIFIED.
                verification = self.verifier(repository, finding, proposal)
                if not verification.verified:
                    errors.append(f"verification failed: {verification.as_dict()}")
                    self._reset(repository)
                    continue

                return RemediationResult(
                    status="verified",
                    attempts=attempt,
                    changed_files=changed,
                    explanation=proposal.explanation,
                )
            except Exception as exc:
                errors.append(str(exc))
                self._reset(repository)

        return RemediationResult(
            status="failed",
            attempts=self.max_attempts,
            changed_files=(),
            explanation="",
            error="; ".join(errors),
        )

    def _reset(self, repository: Path):
        subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=repository,
                       capture_output=True, text=True, check=False)
        subprocess.run(["git", "clean", "-fd"], cwd=repository,
                       capture_output=True, text=True, check=False)
