from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import create_engine, String, Integer, Text, DateTime, Enum, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from packages.jobs.state import JobState


class Base(DeclarativeBase):
    pass


class JobModel(Base):
    __tablename__ = "remediation_jobs"

    job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    repository: Mapped[str] = mapped_column(String(255), nullable=False)
    delivery_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    commit_sha: Mapped[str] = mapped_column(String(40), nullable=False)
    state: Mapped[JobState] = mapped_column(Enum(JobState), nullable=False)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SQLAlchemyJobStore:
    def __init__(self, url: str):
        self.engine = create_engine(url, future=True)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def create(self, job):
        now = datetime.now(timezone.utc)
        model = JobModel(
            job_id=job.job_id,
            repository=job.repository,
            delivery_id=job.delivery_id,
            commit_sha=job.commit_sha,
            state=job.state,
            attempt=job.attempt,
            error=job.error,
            created_at=now,
            updated_at=now,
        )
        with Session(self.engine) as session:
            session.add(model)
            session.commit()
        return job

    def get(self, job_id):
        with Session(self.engine) as session:
            model = session.get(JobModel, job_id)
            return self._to_record(model) if model else None

    def update(self, job):
        with Session(self.engine) as session:
            model = session.get(JobModel, job.job_id)
            if not model:
                raise KeyError(job.job_id)
            model.state = job.state
            model.attempt = job.attempt
            model.error = job.error
            model.updated_at = datetime.now(timezone.utc)
            session.commit()
        return job

    def all(self):
        with Session(self.engine) as session:
            return [self._to_record(x) for x in session.scalars(select(JobModel)).all()]

    @staticmethod
    def _to_record(model):
        from packages.jobs.state import JobRecord
        return JobRecord(
            job_id=model.job_id,
            repository=model.repository,
            delivery_id=model.delivery_id,
            commit_sha=model.commit_sha,
            state=model.state,
            attempt=model.attempt,
            error=model.error,
            created_at=model.created_at.isoformat(),
            updated_at=model.updated_at.isoformat(),
        )
