import pytest, json
from packages.llm import OpenAIChatClient, AnthropicChatClient
class R:
    def __enter__(self): return self
    def __exit__(self,*a): return False
    def read(self): return b'{"choices":[{"message":{"content":"{\\"decision\\":\\"no_patch\\"}"}}]}'
@pytest.mark.asyncio
async def test_openai_client(monkeypatch):
    import packages.llm.clients as c
    monkeypatch.setattr(c,"urlopen",lambda *a,**k:R())
    x=await OpenAIChatClient(api_key="k",model="m").complete(system="s",user="u")
    assert json.loads(x)["decision"]=="no_patch"
def test_credentials_required():
    with pytest.raises(Exception): OpenAIChatClient(api_key="",model="")
    with pytest.raises(Exception): AnthropicChatClient(api_key="",model="")
