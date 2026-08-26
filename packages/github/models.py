from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class WebhookEvent(BaseModel):
    event: str
    delivery_id: str
    payload: dict


class FindingRecord(BaseModel):
    fingerprint: str
    rule_id: str
    path: str
    start_line: int
    end_line: int
    severity: str = "unknown"
    repository: str
    commit_sha: str


class CheckoutRequest(BaseModel):
    repository: str
    commit_sha: str
    workspace: str


class PullRequestRequest(BaseModel):
    repository: str
    base_branch: str
    head_branch: str
    title: str
    body: str
    changed_files: list[str] = Field(default_factory=list)
