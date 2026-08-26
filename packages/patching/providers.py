from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from packages.github.auth import sanitize_secret_text
from packages.patching.models import FindingContext, PatchCandidate, PatchDecision
from packages.patching.protocol import build_patch_prompt, parse_patch_response


class HttpLLMError(RuntimeError):
    """Raised when an HTTP LLM completion request fails."""


class ChatClient(Protocol):
    async def complete(self, *, system: str, user: str) -> str: ...


class OpenAIChatClient:
    """Production OpenAI chat completions client using standard library HTTP."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: int = 60,
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model or os.environ.get("PATCHPROOF_LLM_MODEL", "gpt-4o")
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")
        self.timeout_seconds = timeout_seconds

        if not self.api_key:
            raise HttpLLMError("OPENAI_API_KEY is required for OpenAIChatClient")

    async def complete(self, *, system: str, user: str) -> str:
        import asyncio
        return await asyncio.to_thread(self._complete_sync, system, user)

    def _complete_sync(self, system: str, user: str) -> str:
        body = json.dumps({
            "model": self.model,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }).encode("utf-8")

        req = Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "PatchProof-LLM/1.0",
            },
            method="POST",
        )

        try:
            with urlopen(req, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
        except HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace") if hasattr(exc, "read") else ""
            sanitized = sanitize_secret_text(f"OpenAI HTTP {exc.code}: {err_body or exc.reason}")
            raise HttpLLMError(sanitized) from None
        except Exception as exc:
            sanitized = sanitize_secret_text(f"OpenAI request failed: {exc}")
            raise HttpLLMError(sanitized) from None


class AnthropicChatClient:
    """Production Anthropic messages API client using standard library HTTP."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str = "https://api.anthropic.com/v1",
        timeout_seconds: int = 60,
        max_tokens: int = 4096,
    ):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = model or os.environ.get("PATCHPROOF_LLM_MODEL", "claude-3-5-sonnet-20241022")
        self.base_url = (base_url or "https://api.anthropic.com/v1").rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_tokens = max_tokens

        if not self.api_key:
            raise HttpLLMError("ANTHROPIC_API_KEY is required for AnthropicChatClient")

    async def complete(self, *, system: str, user: str) -> str:
        import asyncio
        return await asyncio.to_thread(self._complete_sync, system, user)

    def _complete_sync(self, system: str, user: str) -> str:
        body = json.dumps({
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": 0.1,
            "system": system,
            "messages": [
                {"role": "user", "content": user},
            ],
        }).encode("utf-8")

        req = Request(
            f"{self.base_url}/messages",
            data=body,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
                "User-Agent": "PatchProof-LLM/1.0",
            },
            method="POST",
        )

        try:
            with urlopen(req, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
            content = data.get("content", [])
            return "".join(x.get("text", "") for x in content if x.get("type") == "text")
        except HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace") if hasattr(exc, "read") else ""
            sanitized = sanitize_secret_text(f"Anthropic HTTP {exc.code}: {err_body or exc.reason}")
            raise HttpLLMError(sanitized) from None
        except Exception as exc:
            sanitized = sanitize_secret_text(f"Anthropic request failed: {exc}")
            raise HttpLLMError(sanitized) from None


@dataclass
class StructuredPatchProvider:
    """Provider-neutral structured output patch generator."""

    client: ChatClient
    provider: str
    model_name: str

    async def propose(self, context: FindingContext) -> PatchCandidate:
        system = (
            "You are PatchProof's security patch generator. "
            "Generate only valid JSON adhering strictly to the PatchCandidate schema. "
            "Never claim a patch is verified. Verification is performed externally by the test engine."
        )
        raw = await self.client.complete(
            system=system,
            user=build_patch_prompt(context),
        )
        return parse_patch_response(
            raw,
            provider=self.provider,
            model_name=self.model_name,
        )


@dataclass
class RobustLLMPatchProvider:
    """LLM provider wrapper with automatic deterministic fallback on failure."""

    primary: StructuredPatchProvider
    fallback: Any
    fallback_on_error: bool = True

    async def propose(self, context: FindingContext) -> PatchCandidate:
        try:
            return await self.primary.propose(context)
        except Exception as exc:
            if not self.fallback_on_error:
                raise
            # Safe fallback to deterministic rule-based model
            candidate = await self.fallback.propose(context)
            candidate.rationale = f"LLM generation failed ({sanitize_secret_text(str(exc))}); fell back to deterministic rule engine"
            return candidate
