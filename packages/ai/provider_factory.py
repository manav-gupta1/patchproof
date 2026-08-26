from __future__ import annotations
import os
from packages.ai.providers.openai_compatible import OpenAICompatibleClient
from packages.ai.providers.anthropic import AnthropicClient


def create_model_client():
    provider = os.environ.get("PATCHPROOF_MODEL_PROVIDER", "openai").lower()
    if provider == "openai":
        return OpenAICompatibleClient()
    if provider == "anthropic":
        return AnthropicClient()
    raise ValueError(f"unsupported PATCHPROOF_MODEL_PROVIDER: {provider}")
