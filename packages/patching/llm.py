from __future__ import annotations

import json


class StructuredPatchGenerator:
    def __init__(self, client):
        self.client = client

    def generate(self, finding: dict, context: dict):
        from packages.patching.prompt import SYSTEM_PROMPT, build_patch_prompt
        raw = self.client.generate(
            system=SYSTEM_PROMPT,
            prompt=build_patch_prompt(finding, context),
            response_format="json",
        )
        if isinstance(raw, str):
            raw = json.loads(raw)

        from packages.patching.contracts import PatchProposal
        proposal = PatchProposal(
            diff=raw["diff"],
            changed_files=list(raw["changed_files"]),
            explanation=raw["explanation"],
            security_rationale=raw["security_rationale"],
            assumptions=list(raw.get("assumptions", [])),
            confidence=float(raw.get("confidence", 0)),
            model=str(raw.get("model", "")),
            provider=str(raw.get("provider", "")),
        )
        proposal.validate_shape()
        return proposal
