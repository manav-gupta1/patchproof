from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json


@dataclass(frozen=True)
class Evidence:
    kind: str
    sha256: str
    payload: dict


def verification_evidence(report):
    payload = report.as_dict()
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return Evidence("verification", hashlib.sha256(canonical).hexdigest(), payload)
