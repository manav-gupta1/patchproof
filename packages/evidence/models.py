from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel
from hashlib import sha256
import json


@dataclass(frozen=True)
class EvidenceBundle:
    job_id: str
    commit_sha: str
    patch_sha256: str
    scanner_summary: str
    test_summary: str
    verification_summary: str

    def canonical_bytes(self) -> bytes:
        payload = {
            "job_id": self.job_id,
            "commit_sha": self.commit_sha,
            "patch_sha256": self.patch_sha256,
            "scanner_summary": self.scanner_summary,
            "test_summary": self.test_summary,
            "verification_summary": self.verification_summary,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()

    @property
    def evidence_sha256(self) -> str:
        return sha256(self.canonical_bytes()).hexdigest()

    def validate(self):
        if len(self.commit_sha) != 40:
            raise ValueError("invalid commit SHA")
        if len(self.patch_sha256) != 64:
            raise ValueError("invalid patch digest")
        for value in (
            self.scanner_summary,
            self.test_summary,
            self.verification_summary,
        ):
            if not value.strip():
                raise ValueError("evidence field cannot be empty")


class EvidenceKind(str, Enum):
    ANALYSIS = "analysis"
    EXPLOIT = "exploit"
    PATCH = "patch"
    TEST = "test"


def utc_now():
    return datetime.now(timezone.utc)


def content_hash(content: str) -> str:
    return sha256(content.encode("utf-8")).hexdigest()


class EvidenceArtifact(BaseModel):
    kind: EvidenceKind
    name: str
    media_type: str
    content: str
    sha256: str
    captured_at: datetime


class VerificationEvidence(BaseModel):
    evidence_id: str
    generated_at: datetime
    manifest_sha256: str
    schema_version: str = "1.0"
    repository: str
    commit_sha: str
    finding_fingerprint: str
    model_provider: str
    model_name: str
    verified: bool
    artifacts: list[EvidenceArtifact]
