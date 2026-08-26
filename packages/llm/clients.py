from __future__ import annotations
import json, os
from urllib.request import Request, urlopen

class HttpLLMError(RuntimeError): pass

class OpenAIChatClient:
    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model or os.environ.get("PATCHPROOF_MODEL", "")
        if not self.api_key or not self.model: raise HttpLLMError("OPENAI_API_KEY and PATCHPROOF_MODEL are required")
    async def complete(self, *, system, user):
        import asyncio
        return await asyncio.to_thread(self._complete_sync, system, user)
    def _complete_sync(self, system, user):
        body = json.dumps({"model": self.model, "temperature": 0, "response_format": {"type":"json_object"},
                           "messages":[{"role":"system","content":system},{"role":"user","content":user}]}).encode()
        req = Request("https://api.openai.com/v1/chat/completions", data=body,
                      headers={"Authorization":f"Bearer {self.api_key}","Content-Type":"application/json"}, method="POST")
        try:
            with urlopen(req, timeout=120) as response: data=json.load(response)
        except Exception as exc: raise HttpLLMError(f"OpenAI request failed: {exc}") from exc
        try: return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc: raise HttpLLMError("unexpected OpenAI response shape") from exc

class AnthropicChatClient:
    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = model or os.environ.get("PATCHPROOF_MODEL", "")
        if not self.api_key or not self.model: raise HttpLLMError("ANTHROPIC_API_KEY and PATCHPROOF_MODEL are required")
    async def complete(self, *, system, user):
        import asyncio
        return await asyncio.to_thread(self._complete_sync, system, user)
    def _complete_sync(self, system, user):
        body=json.dumps({"model":self.model,"max_tokens":12000,"temperature":0,"system":system,
                         "messages":[{"role":"user","content":user}]}).encode()
        req=Request("https://api.anthropic.com/v1/messages", data=body,
                    headers={"x-api-key":self.api_key,"anthropic-version":"2023-06-01","Content-Type":"application/json"}, method="POST")
        try:
            with urlopen(req, timeout=120) as response: data=json.load(response)
        except Exception as exc: raise HttpLLMError(f"Anthropic request failed: {exc}") from exc
        try: return "".join(x.get("text","") for x in data["content"] if x.get("type")=="text")
        except (KeyError, TypeError) as exc: raise HttpLLMError("unexpected Anthropic response shape") from exc
