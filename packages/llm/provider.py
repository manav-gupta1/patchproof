from __future__ import annotations

from typing import Protocol

from packages.patching.models import FindingContext, PatchCandidate
from packages.patching.providers import StructuredPatchProvider


class StructuredChatClient(Protocol):
    async def complete(self, *, system: str, user: str) -> str: ...


class LLMRemediationProvider:
    """Thin production boundary around a structured model client."""

    def __init__(self, client: StructuredChatClient, provider: str, model: str) -> None:
        self.provider = provider
        self.model = model
        self.provider_impl = StructuredPatchProvider(
            client=client,
            provider=provider,
            model_name=model,
        )

    async def generate(self, context: FindingContext) -> PatchCandidate:
        return await self.provider_impl.propose(context)
