from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PatchProposal:
    diff: str
    changed_files: list[str]
    explanation: str
    security_rationale: str
    assumptions: list[str] = field(default_factory=list)
    confidence: float = 0.0
    model: str = ""
    provider: str = ""

    def validate_shape(self) -> None:
        if not self.diff.strip():
            raise ValueError("patch diff is empty")
        if not self.changed_files:
            raise ValueError("patch has no changed files")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not self.explanation.strip():
            raise ValueError("patch explanation is required")
        if not self.security_rationale.strip():
            raise ValueError("security rationale is required")
