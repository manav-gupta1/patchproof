from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from packages.patching.apply import PatchApplier
from packages.patching.context import ContextExtractor
from packages.patching.models import FindingContext, PatchCandidate
from packages.patching.provider import PatchModel


@dataclass
class PatchProposal:
    context: FindingContext
    candidate: PatchCandidate
    applied_files: dict[str, str]


class PatchEngine:
    """Generate a candidate and apply it only after path validation."""

    def __init__(
        self,
        model: PatchModel,
        extractor: ContextExtractor | None = None,
        applier: PatchApplier | None = None,
    ) -> None:
        self.model = model
        self.extractor = extractor or ContextExtractor()
        self.applier = applier or PatchApplier()

    async def generate_and_apply(
        self,
        *,
        workspace: str,
        fingerprint: str,
        rule_id: str,
        path: str,
        start_line: int,
        end_line: int,
        severity: str,
    ) -> PatchProposal:
        context = self.extractor.extract(
            workspace=workspace,
            fingerprint=fingerprint,
            rule_id=rule_id,
            path=path,
            start_line=start_line,
            end_line=end_line,
            severity=severity,
        )

        candidate = await self.model.propose(context)
        if not candidate.patch_id:
            candidate.patch_id = str(uuid4())

        applied = self.applier.apply(workspace, candidate)
        candidate.changed_files = list(applied)
        return PatchProposal(
            context=context,
            candidate=candidate,
            applied_files=applied,
        )
