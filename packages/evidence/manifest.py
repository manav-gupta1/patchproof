from __future__ import annotations

import json
import uuid
from hashlib import sha256
from pathlib import Path
from typing import Any

from packages.evidence.models import (
    EvidenceArtifact,
    EvidenceKind,
    VerificationEvidence,
    content_hash,
    utc_now,
)


class EvidenceBuilder:
    """Builds a deterministic, hash-linked verification evidence package."""

    def __init__(
        self,
        *,
        repository: str,
        commit_sha: str,
        finding_fingerprint: str,
        model_provider: str,
        model_name: str,
    ) -> None:
        self.repository = repository
        self.commit_sha = commit_sha
        self.finding_fingerprint = finding_fingerprint
        self.model_provider = model_provider
        self.model_name = model_name
        self.artifacts: list[EvidenceArtifact] = []

    def add(
        self,
        *,
        kind: EvidenceKind,
        name: str,
        content: str,
        media_type: str = "text/plain",
    ) -> EvidenceArtifact:
        artifact = EvidenceArtifact(
            kind=kind,
            name=name,
            media_type=media_type,
            content=content,
            sha256=content_hash(content),
            captured_at=utc_now(),
        )
        self.artifacts.append(artifact)
        return artifact

    def build(self, *, verified: bool) -> VerificationEvidence:
        # The manifest excludes its own hash to make the signed/hashable material
        # deterministic and auditable.
        unsigned = {
            "schema_version": "1.0",
            "repository": self.repository,
            "commit_sha": self.commit_sha,
            "finding_fingerprint": self.finding_fingerprint,
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "verified": verified,
            "artifacts": [a.model_dump(mode="json") for a in self.artifacts],
        }
        canonical = json.dumps(
            unsigned,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        manifest_hash = sha256(canonical.encode("utf-8")).hexdigest()

        return VerificationEvidence(
            evidence_id=str(uuid.uuid4()),
            generated_at=utc_now(),
            manifest_sha256=manifest_hash,
            **unsigned,
        )


class EvidenceStore:
    """Persists evidence as an immutable-style directory.

    The application should write once and treat the resulting directory as
    append-only. A later database layer can index the manifest without changing
    artifact contents.
    """

    def write(self, root: str | Path, evidence: VerificationEvidence) -> Path:
        destination = Path(root) / evidence.evidence_id
        destination.mkdir(parents=True, exist_ok=False)

        for artifact in evidence.artifacts:
            path = destination / artifact.name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(artifact.content, encoding="utf-8")

        manifest = destination / "manifest.json"
        manifest.write_text(
            evidence.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return destination


def verify_evidence(evidence: VerificationEvidence) -> tuple[bool, list[str]]:
    errors: list[str] = []

    unsigned = {
        "schema_version": evidence.schema_version,
        "repository": evidence.repository,
        "commit_sha": evidence.commit_sha,
        "finding_fingerprint": evidence.finding_fingerprint,
        "model_provider": evidence.model_provider,
        "model_name": evidence.model_name,
        "verified": evidence.verified,
        "artifacts": [a.model_dump(mode="json") for a in evidence.artifacts],
    }
    canonical = json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    expected_manifest = sha256(canonical.encode("utf-8")).hexdigest()
    if expected_manifest != evidence.manifest_sha256:
        errors.append("manifest hash mismatch")

    for artifact in evidence.artifacts:
        if content_hash(artifact.content) != artifact.sha256:
            errors.append(f"artifact hash mismatch: {artifact.name}")

    return not errors, errors
