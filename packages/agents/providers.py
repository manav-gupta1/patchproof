from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from pydantic import BaseModel

from packages.agents.models import LLMProvider


class LLMProviderError(RuntimeError):
    pass


class StaticLLMProvider(LLMProvider):
    """Deterministic provider for tests and local development."""

    def __init__(self, response: BaseModel) -> None:
        self.response = response

    async def complete(
        self,
        *,
        system: str,
        user: str,
        response_model: type[BaseModel],
    ) -> BaseModel:
        if not isinstance(self.response, response_model):
            raise TypeError(
                f"Static response is {type(self.response).__name__}, "
                f"expected {response_model.__name__}"
            )
        return self.response


class OpenAICompatibleProvider(LLMProvider):
    """Minimal OpenAI-compatible HTTP provider.

    The provider is intentionally vendor-neutral. Configure base_url, API key,
    and model through the ModelRouter rather than coupling agents to a vendor.
    """

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 60.0,
        max_retries: int = 2,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    async def complete(
        self,
        *,
        system: str,
        user: str,
        response_model: type[BaseModel],
    ) -> BaseModel:
        try:
            import httpx
        except ImportError as exc:
            raise LLMProviderError("httpx is required for production LLM providers") from exc

        schema = response_model.model_json_schema()
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": response_model.__name__,
                    "strict": True,
                    "schema": schema,
                },
            },
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                    response.raise_for_status()
                    body = response.json()
                    content = body["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    return response_model.model_validate(parsed)
            except (httpx.HTTPError, KeyError, IndexError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5 * (2**attempt))
                    continue
                break

        raise LLMProviderError(
            f"LLM request failed after {self.max_retries + 1} attempts"
        ) from last_error


class MockReasoningProvider(StaticLLMProvider):
    """Explicitly named deterministic provider for integration tests."""
    pass
