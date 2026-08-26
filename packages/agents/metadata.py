from __future__ import annotations

from datetime import datetime, timezone
from pydantic import BaseModel, Field


class ModelInvocation(BaseModel):
    request_id: str
    route: str
    provider: str
    model: str
    started_at: datetime
    completed_at: datetime
    attempts: int = Field(ge=1)
    success: bool
    response_schema: str


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
