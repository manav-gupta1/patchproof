from __future__ import annotations

from dataclasses import asdict
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, select, update
from packages.github.transaction import PublicationPhase, PublicationRecord


class DurablePublicationRecordStore:
    def __init__(self, engine):
        self.engine = engine
        self.metadata = MetaData()
        self.records = Table(
            "publication_transactions",
            self.metadata,
            Column("job_id", String(255), primary_key=True),
            Column("evidence_sha256", String(64), nullable=False),
            Column("branch", String(255), nullable=False),
            Column("commit_sha", String(40), nullable=False),
            Column("phase", String(32), nullable=False),
            Column("pr_number", Integer, nullable=True),
            Column("pr_url", String(2048), nullable=True),
        )

    def create_schema(self):
        self.metadata.create_all(self.engine)

    def get(self, job_id):
        with self.engine.begin() as conn:
            row = conn.execute(
                select(self.records).where(self.records.c.job_id == job_id)
            ).mappings().first()
        if row is None:
            return None
        return PublicationRecord(
            job_id=row["job_id"],
            evidence_sha256=row["evidence_sha256"],
            branch=row["branch"],
            commit_sha=row["commit_sha"],
            phase=PublicationPhase(row["phase"]),
            pr_number=row["pr_number"],
            pr_url=row["pr_url"],
        )

    def put(self, record):
        values = {
            "job_id": record.job_id,
            "evidence_sha256": record.evidence_sha256,
            "branch": record.branch,
            "commit_sha": record.commit_sha,
            "phase": record.phase.value,
            "pr_number": record.pr_number,
            "pr_url": record.pr_url,
        }
        with self.engine.begin() as conn:
            existing = conn.execute(
                select(self.records.c.job_id).where(
                    self.records.c.job_id == record.job_id
                )
            ).first()
            if existing:
                conn.execute(
                    update(self.records)
                    .where(self.records.c.job_id == record.job_id)
                    .values(**values)
                )
            else:
                conn.execute(self.records.insert().values(**values))


def create_durable_store(url="sqlite:///patchproof.db"):
    engine = create_engine(url)
    store = DurablePublicationRecordStore(engine)
    store.create_schema()
    return store
