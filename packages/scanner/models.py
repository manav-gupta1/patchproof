from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FindingLocation(BaseModel):
    file: str
    start_line: int = Field(ge=1)
    start_column: int | None = Field(default=None, ge=1)
    end_line: int | None = Field(default=None, ge=1)
    end_column: int | None = Field(default=None, ge=1)


class NormalizedFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fingerprint: str
    rule_id: str
    severity: str
    message: str
    language: str
    location: FindingLocation
    repository: str | None = None
    commit_sha: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    raw: dict[str, Any] = Field(default_factory=dict)
    received_at: datetime | None = None
