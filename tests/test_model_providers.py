import json
from unittest.mock import patch
from packages.ai.providers.openai_compatible import OpenAICompatibleClient
from packages.ai.providers.anthropic import AnthropicClient


class FakeResponse:
    def __init__(self, data):
        self.data = json.dumps(data).encode()
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self): return self.data
    def __iter__(self): return iter([self.data])


def test_openai_compatible_client_parses_response():
    data = {"choices": [{"message": {"content": '{"ok": true}'}}]}
    with patch("packages.ai.providers.openai_compatible.urlopen", return_value=FakeResponse(data)):
        out = OpenAICompatibleClient(api_key="test", model="test").complete(system="s", user="u")
    assert out == '{"ok": true}'


def test_anthropic_client_parses_text_blocks():
    data = {"content": [{"type": "text", "text": '{"ok": true}'}]}
    with patch("packages.ai.providers.anthropic.urlopen", return_value=FakeResponse(data)):
        out = AnthropicClient(api_key="test", model="test").complete(system="s", user="u")
    assert out == '{"ok": true}'
