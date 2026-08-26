from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json


@dataclass(frozen=True)
class ExecutionArtifact:
    kind: str
    name: str
    content: str

    @property
    def sha256(self):
        return sha256(self.content.encode()).hexdigest()


@dataclass(frozen=True)
class ExecutionEvidence:
    scanner: ExecutionArtifact
    tests: ExecutionArtifact
    verification: ExecutionArtifact

    def canonical_bytes(self):
        payload = {
            "scanner": {"kind": self.scanner.kind, "name": self.scanner.name,
                        "sha256": self.scanner.sha256},
            "tests": {"kind": self.tests.kind, "name": self.tests.name,
                      "sha256": self.tests.sha256},
            "verification": {"kind": self.verification.kind,
                             "name": self.verification.name,
                             "sha256": self.verification.sha256},
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()

    @property
    def evidence_sha256(self):
        return sha256(self.canonical_bytes()).hexdigest()

    def validate(self):
        for artifact in (self.scanner, self.tests, self.verification):
            if not artifact.content.strip():
                raise ValueError(f"empty execution artifact: {artifact.name}")
            if not artifact.kind.strip() or not artifact.name.strip():
                raise ValueError("execution artifact metadata is incomplete")
