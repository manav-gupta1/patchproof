from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from packages.state.machine import JobState


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class StateTransition:
    from_state: JobState
    to_state: JobState
    actor: str
    reason: str
    occurred_at: datetime = field(default_factory=utcnow)


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    kind: str
    sha256: str
    payload: dict[str, Any]
    created_at: datetime = field(default_factory=utcnow)


@dataclass
class Job:
    job_id: str
    repository: str
    commit_sha: str
    finding_fingerprint: str
    state: JobState = JobState.RECEIVED
    transitions: list[StateTransition] = field(default_factory=list)
    evidence: list[EvidenceRecord] = field(default_factory=list)

    def add_evidence(self, evidence: EvidenceRecord) -> None:
        if any(x.evidence_id == evidence.evidence_id for x in self.evidence):
            raise ValueError(f"duplicate evidence id: {evidence.evidence_id}")
        self.evidence.append(evidence)
