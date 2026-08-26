from __future__ import annotations

from dataclasses import dataclass

from packages.agents.models import LLMProvider


@dataclass(frozen=True)
class ModelRoute:
    name: str
    provider: LLMProvider
    model: str
    purpose: str


class ModelRouter:
    """Routes work by purpose rather than hard-coding a model into agents."""

    def __init__(self, *, triage: ModelRoute, reasoning: ModelRoute) -> None:
        self._routes = {
            "triage": triage,
            "reasoning": reasoning,
        }

    def route(self, purpose: str) -> ModelRoute:
        try:
            return self._routes[purpose]
        except KeyError as exc:
            raise ValueError(f"Unsupported model route: {purpose}") from exc

    def provider_for(self, purpose: str) -> LLMProvider:
        return self.route(purpose).provider
