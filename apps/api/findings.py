from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from packages.scanner import SemgrepAdapter, SemgrepPayloadError

router = APIRouter(prefix="/v1/findings", tags=["findings"])


async def _session_dependency() -> AsyncIterator[Any]:
    from packages.database.session import get_session

    async for session in get_session():
        yield session


@router.post("/semgrep")
async def ingest_semgrep(payload: dict, session: Any = Depends(_session_dependency)) -> dict:
    from sqlalchemy import select
    from packages.database.models import Finding

    try:
        findings = SemgrepAdapter().parse(payload)
    except SemgrepPayloadError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    created: list[str] = []
    for finding in findings:
        existing = await session.scalar(select(Finding).where(Finding.fingerprint == finding.fingerprint))
        if existing is None:
            record = Finding(
                fingerprint=finding.fingerprint,
                rule_id=finding.rule_id,
                severity=finding.severity,
                message=finding.message,
                language=finding.language,
                file=finding.location.file,
                start_line=finding.location.start_line,
                end_line=finding.location.end_line or finding.location.start_line,
                extra_metadata=finding.metadata,
                raw_semgrep=finding.raw,
            )
            session.add(record)
            await session.flush()
            created.append(str(record.id))
        else:
            created.append(str(existing.id))

    await session.commit()
    return {"count": len(findings), "finding_ids": created}
