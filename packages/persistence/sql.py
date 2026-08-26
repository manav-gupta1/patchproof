from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from packages.persistence.models import JobState, RemediationJob


class Base(DeclarativeBase):
    pass


class JobRow(Base):
    __tablename__ = "remediation_jobs"

    id: Mapped[str] = mapped_column(String(200), primary_key=True)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    repository: Mapped[str] = mapped_column(String(500), nullable=False)
    commit_sha: Mapped[str] = mapped_column(String(200), nullable=False)
    finding_fingerprint: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    error: Mapped[str | None] = mapped_column(String(4000), nullable=True)


class SqlJobRepository:
    def __init__(self, url: str) -> None:
        self.engine = create_engine(url, future=True)

    def create_schema(self) -> None:
        Base.metadata.create_all(self.engine)

    def create(self, job: RemediationJob) -> RemediationJob:
        with Session(self.engine) as session:
            if session.get(JobRow, job.id) is not None:
                raise ValueError("job already exists")
            data = job.model_dump()
            row = JobRow(
                id=data["id"],
                state=data["state"].value if hasattr(data["state"], "value") else data["state"],
                repository=data["repository"],
                commit_sha=data["commit_sha"],
                finding_fingerprint=data["finding_fingerprint"],
                created_at=data["created_at"],
                updated_at=data["updated_at"],
                attempts=data.get("attempt", 0),
                error=data.get("failure_message"),
            )
            session.add(row)
            session.commit()
        return job

    def get(self, job_id: str) -> RemediationJob | None:
        with Session(self.engine) as session:
            row = session.get(JobRow, job_id)
            if row is None:
                return None
            return RemediationJob(
                id=row.id,
                state=JobState(row.state),
                repository=row.repository,
                commit_sha=row.commit_sha,
                finding_fingerprint=row.finding_fingerprint,
                created_at=row.created_at,
                updated_at=row.updated_at,
                attempts=row.attempts,
                error=row.error,
            )

    def transition(self, job_id: str, state: JobState) -> RemediationJob:
        with Session(self.engine) as session:
            row = session.get(JobRow, job_id)
            if row is None:
                raise KeyError(job_id)
            row.state = state.value
            row.updated_at = datetime.now(timezone.utc)
            session.commit()
        result = self.get(job_id)
        assert result is not None
        return result
