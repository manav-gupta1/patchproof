from __future__ import annotations

import hashlib
import json
from typing import Any

from packages.state.models import EvidenceRecord


def make_evidence(kind: str, payload: dict[str, Any]) -> EvidenceRecord:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    return EvidenceRecord(
        evidence_id=f"{kind}:{digest[:20]}",
        kind=kind,
        sha256=digest,
        payload=payload,
    )
