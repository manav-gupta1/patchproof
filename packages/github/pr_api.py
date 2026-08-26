from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class GitHubAPI(Protocol):
    def create_pull_request(self, *, owner: str, repo: str, title: str,
                             body: str, head: str, base: str) -> dict: ...


@dataclass(frozen=True)
class PRCreationResult:
    url: str
    number: int | None
    owner: str
    repo: str
    head: str
    base: str


class GitHubPRCreator:
    def __init__(self, api: GitHubAPI):
        self.api = api

    def create_verified_pr(
        self, *, verified: bool, owner: str, repo: str,
        title: str, body: str, head: str, base: str
    ) -> PRCreationResult:
        if not verified:
            raise ValueError("only VERIFIED remediations may create pull requests")
        if not all([owner, repo, title, body, head, base]):
            raise ValueError("incomplete pull request request")

        result = self.api.create_pull_request(
            owner=owner, repo=repo, title=title, body=body,
            head=head, base=base,
        )
        url = result.get("html_url")
        if not url:
            raise RuntimeError("GitHub did not return pull request URL")

        return PRCreationResult(
            url=url,
            number=result.get("number"),
            owner=owner,
            repo=repo,
            head=head,
            base=base,
        )
