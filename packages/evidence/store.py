from __future__ import annotations
from sqlalchemy import DateTime, Integer, String, Text, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from datetime import datetime, timezone

from packages.evidence.models import EvidenceBundle


class EvidenceBase(DeclarativeBase):
    pass


class EvidenceModel(EvidenceBase):
    __tablename__ = "evidence_bundles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    commit_sha: Mapped[str] = mapped_column(String(40))
    patch_sha256: Mapped[str] = mapped_column(String(64))
    scanner_summary: Mapped[str] = mapped_column(Text)
    test_summary: Mapped[str] = mapped_column(Text)
    verification_summary: Mapped[str] = mapped_column(Text)
    evidence_sha256: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class EvidenceStore:
    def __init__(self, engine=None):
        self.engine = engine


    def write(self, root, evidence):
        destination = Path(root) / getattr(evidence, "evidence_id", "evidence")
        destination.mkdir(parents=True, exist_ok=True)
        if hasattr(evidence, "model_dump_json"):
            (destination / "manifest.json").write_text(
                evidence.model_dump_json(indent=2), encoding="utf-8"
            )
        elif hasattr(evidence, "as_dict"):
            import json
            (destination / "manifest.json").write_text(
                json.dumps(evidence.as_dict(), indent=2, sort_keys=True),
                encoding="utf-8",
            )
        return destination

    def create_schema(self):
        EvidenceBase.metadata.create_all(self.engine)

    def put(self, bundle: EvidenceBundle):
        bundle.validate()
        with Session(self.engine, expire_on_commit=False) as session:
            existing = session.scalar(
                select(EvidenceModel).where(EvidenceModel.job_id == bundle.job_id)
            )
            if existing:
                if existing.evidence_sha256 != bundle.evidence_sha256:
                    raise ValueError("evidence already exists with different content")
                return existing

            row = EvidenceModel(
                job_id=bundle.job_id,
                commit_sha=bundle.commit_sha,
                patch_sha256=bundle.patch_sha256,
                scanner_summary=bundle.scanner_summary,
                test_summary=bundle.test_summary,
                verification_summary=bundle.verification_summary,
                evidence_sha256=bundle.evidence_sha256,
            )
            session.add(row)
            session.commit()
            return row

    def put_execution(self, job_id: str, execution):
        execution.validate()
        return execution.evidence_sha256

    def get(self, job_id: str) -> EvidenceBundle | None:
        with Session(self.engine, expire_on_commit=False) as session:
            row = session.scalar(
                select(EvidenceModel).where(EvidenceModel.job_id == job_id)
            )
            if row is None:
                return None
            return EvidenceBundle(
                job_id=row.job_id,
                commit_sha=row.commit_sha,
                patch_sha256=row.patch_sha256,
                scanner_summary=row.scanner_summary,
                test_summary=row.test_summary,
                verification_summary=row.verification_summary,
            )
