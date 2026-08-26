from __future__ import annotations

import json
from typing import Any

from packages.agents.models import AnalystRequest, LLMProvider, VulnerabilityAnalysis


ANALYST_SYSTEM_PROMPT = """You are PatchProof's vulnerability analyst.
Analyze a Semgrep finding using only the supplied repository context. Treat the Semgrep result as a hypothesis, not proof.
Do not invent files, data-flow edges, runtime behavior, or exploitability facts. Preserve uncertainty.
Return only structured data matching the requested schema. `eligible` means there is enough evidence to proceed to executable exploit and patch generation.
This stage must never claim that a patch is fixed or verified."""


class AnalystAgent:
    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    async def analyze(self, request: AnalystRequest) -> VulnerabilityAnalysis:
        result = await self.provider.complete(
            system=ANALYST_SYSTEM_PROMPT,
            user=self._build_prompt(request),
            response_model=VulnerabilityAnalysis,
        )
        if not isinstance(result, VulnerabilityAnalysis):
            raise TypeError("LLM provider returned an unexpected analyst response")
        if result.finding_fingerprint != request.finding.fingerprint:
            raise ValueError("Analyst response fingerprint does not match the finding")
        return result

    @staticmethod
    def _build_prompt(request: AnalystRequest) -> str:
        payload: dict[str, Any] = {
            "finding": request.finding.model_dump(mode="json"),
            "repository_context": request.context.model_dump(mode="json") if hasattr(request.context, "model_dump") else vars(request.context),
        }
        return "Analyze this finding and preserve uncertainty.\n\n" + json.dumps(payload, indent=2, sort_keys=True)
