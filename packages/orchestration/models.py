from __future__ import annotations

from enum import Enum
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class JobState(str, Enum):
    RECEIVED = "received"
    ANALYZING = "analyzing"
    EXPLOITING = "exploiting"
    PATCHING = "patching"
    VERIFYING = "verifying"
    VERIFIED = "verified"
    PR_CREATED = "pr_created"
    FAILED = "failed"


class FailureCode(str, Enum):
    INVALID_EVENT = "invalid_event"
    CHECKOUT_FAILED = "checkout_failed"
    ANALYSIS_FAILED = "analysis_failed"
    NOT_ELIGIBLE = "not_eligible"
    EXPLOIT_FAILED = "exploit_failed"
    PATCH_FAILED = "patch_failed"
    VERIFICATION_FAILED = "verification_failed"
    PR_FAILED = "pr_failed"
    INTERNAL_ERROR = "internal_error"


class RemediationJob(BaseModel):
    id: str
    state: JobState
    repository: str
    commit_sha: str
    finding_fingerprint: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    failure_code: FailureCode | None = None
    failure_message: str | None = None
    evidence_id: str | None = None
    pull_request_url: str | None = None
    attempt: int = 0
