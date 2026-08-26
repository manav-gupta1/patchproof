from __future__ import annotations
import json
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError


class AnthropicClient:
    def __init__(self, api_key=None, model=None, base_url="https://api.anthropic.com", timeout=90):
        self.api_key = api_key or os.environ["ANTHROPIC_API_KEY"]
        self.model = model or os.environ.get("PATCHPROOF_ANTHROPIC_MODEL", "claude-sonnet-4-6")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def complete(self, *, system: str, user: str) -> str:
        payload = {
            "model": self.model,
            "max_tokens": 8000,
            "temperature": 0,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        req = Request(
            self.base_url + "/v1/messages",
            data=json.dumps(payload).encode(),
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(req, timeout=self.timeout) as response:
                data = json.load(response)
        except HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise RuntimeError(f"model provider HTTP {exc.code}: {detail}") from exc
        try:
            blocks = data["content"]
            return "".join(block["text"] for block in blocks if block.get("type") == "text")
        except (KeyError, TypeError) as exc:
            raise RuntimeError("model provider returned an unexpected response") from exc
