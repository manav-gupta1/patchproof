from __future__ import annotations

import json

from packages.agents.models import LLMProvider
from packages.patching.models import PatchCandidate, PatchRequest


PATCH_SYSTEM_PROMPT = """You are PatchProof's security patch generator.

Generate the smallest defensible source patch for the analyzed vulnerability.

Rules:
- Use only files and source supported by the supplied context.
- Prefer minimal changes over refactors.
- Preserve existing public behavior except where necessary to remove the vulnerability.
- Do not change tests merely to make them pass.
- Do not weaken, delete, or disable security checks.
- Every operation must use exact old_text from the supplied context.
- Never claim verification; the verification engine decides whether a patch works.
- If the evidence is insufficient to construct an exact patch, return the best candidate
  only when the required source text is actually present.

Return only data matching the requested structured schema.
"""


class PatchAgent:
    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    async def generate(self, request: PatchRequest) -> PatchCandidate:
        payload = {
            "analysis": request.analysis.model_dump(mode="json"),
            "context": request.context.model_dump(mode="json"),
            "exploit_success_evidence": request.exploit_success_evidence,
        }
        result = await self.provider.complete(
            system=PATCH_SYSTEM_PROMPT,
            user=json.dumps(payload, indent=2, sort_keys=True),
            response_model=PatchCandidate,
        )
        if not isinstance(result, PatchCandidate):
            raise TypeError("LLM provider returned an unexpected patch candidate")
        if result.finding_fingerprint != request.analysis.finding_fingerprint:
            raise ValueError("Patch fingerprint does not match analyzed finding")
        return result
