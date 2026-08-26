from __future__ import annotations

import json

from packages.evidence import EvidenceBuilder, EvidenceKind
from packages.sandbox.models import ExecutionResult


def add_execution_evidence(
    builder: EvidenceBuilder,
    *,
    name: str,
    result: ExecutionResult,
) -> None:
    builder.add(
        kind=EvidenceKind.TEST,
        name=f"{name}.json",
        content=json.dumps(result.model_dump(mode="json"), indent=2),
        media_type="application/json",
    )
    builder.add(
        kind=EvidenceKind.TEST,
        name=f"{name}.stdout.txt",
        content=result.stdout,
    )
    builder.add(
        kind=EvidenceKind.TEST,
        name=f"{name}.stderr.txt",
        content=result.stderr,
    )
