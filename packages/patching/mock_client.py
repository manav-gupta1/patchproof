from __future__ import annotations


class StaticChatClient:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list[dict[str, str]] = []

    async def complete(self, *, system: str, user: str) -> str:
        self.calls.append({"system": system, "user": user})
        return self.response
