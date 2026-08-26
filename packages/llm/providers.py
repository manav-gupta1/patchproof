from __future__ import annotations
import json
import os
from urllib.request import Request, urlopen


class OpenAIProvider:
    def __init__(self, api_key=None, model="gpt-5-nano", base_url="https://api.openai.com/v1"):
        self.api_key = api_key or os.environ["OPENAI_API_KEY"]
        self.model = model
        self.base_url = base_url.rstrip("/")

    def __call__(self, payload):
        body = {
            "model": self.model,
            "input": json.dumps(payload, separators=(",", ":")),
        }
        req = Request(
            self.base_url + "/responses",
            data=json.dumps(body).encode(),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urlopen(req, timeout=120) as response:
            data = json.loads(response.read())
        # Keep provider parsing isolated; callers receive plain text.
        if "output_text" in data:
            return data["output_text"]
        return json.dumps(data)


class AnthropicProvider:
    def __init__(self, api_key=None, model="claude-sonnet-4-6",
                 base_url="https://api.anthropic.com/v1"):
        self.api_key = api_key or os.environ["ANTHROPIC_API_KEY"]
        self.model = model
        self.base_url = base_url.rstrip("/")

    def __call__(self, payload):
        body = {
            "model": self.model,
            "max_tokens": 8192,
            "messages": [{
                "role": "user",
                "content": json.dumps(payload, separators=(",", ":")),
            }],
        }
        req = Request(
            self.base_url + "/messages",
            data=json.dumps(body).encode(),
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            method="POST",
        )
        with urlopen(req, timeout=180) as response:
            data = json.loads(response.read())
        content = data.get("content", [])
        return "".join(x.get("text", "") for x in content if x.get("type") == "text")
