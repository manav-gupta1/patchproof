from __future__ import annotations
import json
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError


class OpenAICompatibleClient:
    """Small stdlib-only client for OpenAI-compatible chat APIs."""

    def __init__(self, api_key=None, model=None, base_url=None, timeout=90):
        self.api_key = api_key or os.environ["OPENAI_API_KEY"]
        self.model = model or os.environ.get("PATCHPROOF_MODEL", "gpt-5-nano")
        self.base_url = (base_url or os.environ.get(
            "PATCHPROOF_OPENAI_BASE_URL", "https://api.openai.com/v1"
        )).rstrip("/")
        self.timeout = timeout

    def complete(self, *, system: str, user: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0,
        }
        req = Request(
            self.base_url + "/chat/completions",
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {self.api_key}",
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
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("model provider returned an unexpected response") from exc
