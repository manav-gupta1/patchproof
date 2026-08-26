from __future__ import annotations

from pydantic import BaseModel


class RemediationTask(BaseModel):
    job_id: str
    repository: str
    commit_sha: str
    finding_fingerprint: str
    rule_id: str
    path: str
    start_line: int
    end_line: int
    severity: str
