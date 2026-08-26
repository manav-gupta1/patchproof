from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import json
import hashlib


@dataclass(frozen=True)
class EvidenceBundle:
    job_id: str
    finding: dict
    patch: dict
    baseline: dict
    patched: dict
    tests: dict
    semgrep: dict
    verification: dict
    verified: bool
    created_at: str

    def as_dict(self):
        return asdict(self)


class EvidenceBuilder:
    def build(self, *, job_id, finding, patch, baseline, patched, tests, semgrep,
              verification=None):
        verification = verification or {}
        verified = bool(verification.get("verified", (
            baseline.get("exploit_reproduced") is True
            and patched.get("exploit_reproduced") is False
            and tests.get("passed") is True
            and semgrep.get("finding_count", 1) == 0
        )))
        return EvidenceBundle(
            job_id=job_id,
            finding=finding,
            patch=patch,
            baseline=baseline,
            patched=patched,
            tests=tests,
            semgrep=semgrep,
            verification=verification,
            verified=verified,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def write(self, bundle, path):
        path.write_text(json.dumps(bundle.as_dict(), indent=2, sort_keys=True))
        return path


@dataclass(frozen=True)
class EvidenceArtifact:
    name: str
    sha256: str
    size: int


class EvidenceBundleBuilder:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._artifacts = []

    def add_text(self, name, text):
        data = text.encode("utf-8")
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        artifact = EvidenceArtifact(name, digest, len(data))
        self._artifacts.append(artifact)
        return artifact

    def manifest(self, *, finding, patch, verification, environment):
        return {
            "schema_version": "1.0",
            "artifacts": [asdict(a) for a in self._artifacts],
            "finding": finding,
            "patch": patch,
            "verification": verification,
            "environment": environment,
        }

    def write_manifest(self, manifest):
        path = self.root / "manifest.json"
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
        return path
