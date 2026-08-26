from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class GitHubPRPayloadBuilder:
    owner: str
    repo: str
    base: str
    head: str
    title: str
    body: str

    def build(self) -> dict:
        if not self.owner or not self.repo or not self.base or not self.head:
            raise ValueError("incomplete PR target")
        return {
            "owner": self.owner,
            "repo": self.repo,
            "base": self.base,
            "head": self.head,
            "title": self.title,
            "body": self.body,
        }
