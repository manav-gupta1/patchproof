from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
    select,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class JobModel(Base):
    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    delivery_id: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    repository: Mapped[str] = mapped_column(String(512))
    commit_sha: Mapped[str] = mapped_column(String(64))
    event_type: Mapped[str] = mapped_column(String(128))
    target_branch: Mapped[str | None] = mapped_column(String(256), nullable=True)
    installation_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    check_run_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    state: Mapped[str] = mapped_column(String(64), default="queued")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    pr_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    policy_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    pr_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pr_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    remediation_branch: Mapped[str | None] = mapped_column(String(256), nullable=True)
    current_head_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    verified_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    merge_commit_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_stale: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)
    invalidation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    invalidated_by_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=True,
    )


class JobEventModel(Base):
    __tablename__ = "job_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[str] = mapped_column(String(128), index=True)
    from_state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    to_state: Mapped[str] = mapped_column(String(64))
    message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class RepositoryPolicyModel(Base):
    __tablename__ = "repository_policies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    repository: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    policy_data: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=True,
    )


class RepositoryModel(Base):
    __tablename__ = "repositories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    repository: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    owner: Mapped[str] = mapped_column(String(256))
    name: Mapped[str] = mapped_column(String(256))
    provider: Mapped[str] = mapped_column(String(64), default="github")
    default_branch: Mapped[str] = mapped_column(String(256), default="main")
    installation_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(64), default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=True,
    )


@dataclass
class StoredJob:
    job_id: str
    delivery_id: str
    repository: str
    commit_sha: str
    event_type: str
    state: str = "queued"
    attempt: int = 1
    error: str | None = None
    pr_data: str | None = None
    evidence_data: str | None = None
    policy_data: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    installation_id: int | None = None
    check_run_id: int | None = None
    target_branch: str | None = None
    pr_number: int | None = None
    pr_url: str | None = None
    remediation_branch: str | None = None
    current_head_sha: str | None = None
    verified_sha: str | None = None
    merge_commit_sha: str | None = None
    is_stale: bool = False
    invalidation_reason: str | None = None
    invalidated_by_sha: str | None = None

    @property
    def pr(self) -> dict[str, Any] | None:
        if self.pr_data:
            try:
                return json.loads(self.pr_data)
            except Exception:
                return None
        return None

    @property
    def evidence(self) -> dict[str, Any] | None:
        if self.evidence_data:
            try:
                return json.loads(self.evidence_data)
            except Exception:
                return None
        return None

    @property
    def policy_decision(self) -> dict[str, Any] | None:
        if self.policy_data:
            try:
                return json.loads(self.policy_data)
            except Exception:
                return None
        return None


class PostgresJobStore:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, pool_pre_ping=True)

    def create_schema(self):
        from sqlalchemy import inspect
        import sqlalchemy as sa
        Base.metadata.create_all(self.engine)
        # Migrate SQLite / dynamic engines if new columns are missing
        try:
            with self.engine.connect() as conn:
                insp = inspect(conn)
                if "jobs" in insp.get_table_names():
                    cols = [c["name"] for c in insp.get_columns("jobs")]
                    if "check_run_id" not in cols:
                        conn.execute(sa.text("ALTER TABLE jobs ADD COLUMN check_run_id BIGINT"))
                    if "policy_data" not in cols:
                        conn.execute(sa.text("ALTER TABLE jobs ADD COLUMN policy_data TEXT"))
                    if "target_branch" not in cols:
                        conn.execute(sa.text("ALTER TABLE jobs ADD COLUMN target_branch VARCHAR(256)"))
                    if "pr_number" not in cols:
                        conn.execute(sa.text("ALTER TABLE jobs ADD COLUMN pr_number INTEGER"))
                    if "pr_url" not in cols:
                        conn.execute(sa.text("ALTER TABLE jobs ADD COLUMN pr_url VARCHAR(512)"))
                    if "remediation_branch" not in cols:
                        conn.execute(sa.text("ALTER TABLE jobs ADD COLUMN remediation_branch VARCHAR(256)"))
                    if "current_head_sha" not in cols:
                        conn.execute(sa.text("ALTER TABLE jobs ADD COLUMN current_head_sha VARCHAR(64)"))
                    if "verified_sha" not in cols:
                        conn.execute(sa.text("ALTER TABLE jobs ADD COLUMN verified_sha VARCHAR(64)"))
                    if "merge_commit_sha" not in cols:
                        conn.execute(sa.text("ALTER TABLE jobs ADD COLUMN merge_commit_sha VARCHAR(64)"))
                    if "is_stale" not in cols:
                        conn.execute(sa.text("ALTER TABLE jobs ADD COLUMN is_stale BOOLEAN DEFAULT FALSE"))
                    if "invalidation_reason" not in cols:
                        conn.execute(sa.text("ALTER TABLE jobs ADD COLUMN invalidation_reason TEXT"))
                    if "invalidated_by_sha" not in cols:
                        conn.execute(sa.text("ALTER TABLE jobs ADD COLUMN invalidated_by_sha VARCHAR(64)"))
                    conn.commit()
        except Exception:
            pass

    def exists_delivery(self, delivery_id: str) -> bool:
        with Session(self.engine) as session:
            return session.scalar(
                select(JobModel.id).where(JobModel.delivery_id == delivery_id)
            ) is not None

    def create_from_webhook(
        self,
        *,
        delivery_id,
        repository,
        commit_sha,
        event_type,
        installation_id=None,
        check_run_id=None,
        target_branch=None,
        policy_decision=None,
    ):
        with Session(self.engine) as session:
            existing = session.scalar(
                 select(JobModel).where(JobModel.delivery_id == delivery_id)
            )
            if existing:
                return StoredJob(
                    job_id=existing.job_id,
                    delivery_id=existing.delivery_id,
                    repository=existing.repository,
                    commit_sha=existing.commit_sha,
                    event_type=existing.event_type,
                    state=existing.state,
                    error=existing.error,
                    pr_data=existing.pr_data,
                    evidence_data=existing.evidence_data,
                    policy_data=existing.policy_data,
                    created_at=existing.created_at,
                    updated_at=existing.updated_at,
                    installation_id=existing.installation_id,
                    check_run_id=existing.check_run_id,
                    target_branch=existing.target_branch,
                )

            now = datetime.now(timezone.utc)
            job_id = f"job-{delivery_id}"
            policy_str = json.dumps(policy_decision) if isinstance(policy_decision, dict) else (str(policy_decision) if policy_decision else None)
            job = JobModel(
                job_id=job_id,
                delivery_id=delivery_id,
                repository=repository,
                commit_sha=commit_sha,
                event_type=event_type,
                target_branch=target_branch,
                installation_id=installation_id,
                check_run_id=check_run_id,
                policy_data=policy_str,
                state="queued",
                created_at=now,
                updated_at=now,
            )
            session.add(job)
            session.add(JobEventModel(
                job_id=job_id,
                from_state=None,
                to_state="queued",
                message="created from GitHub webhook",
                created_at=now,
            ))
            session.commit()
            return StoredJob(
                job_id=job_id,
                delivery_id=delivery_id,
                repository=repository,
                commit_sha=commit_sha,
                event_type=event_type,
                state="queued",
                created_at=now,
                updated_at=now,
                installation_id=installation_id,
                check_run_id=check_run_id,
                target_branch=target_branch,
                policy_data=policy_str,
            )

    def save_check_run_id(self, job_id: str, check_run_id: int) -> None:
        with Session(self.engine) as session:
            job = session.scalar(select(JobModel).where(JobModel.job_id == job_id))
            if job:
                job.check_run_id = check_run_id
                job.updated_at = datetime.now(timezone.utc)
                session.commit()

    def save_policy_decision(self, job_id: str, decision: dict[str, Any]) -> None:
        with Session(self.engine) as session:
            job = session.scalar(select(JobModel).where(JobModel.job_id == job_id))
            if job:
                job.policy_data = json.dumps(decision) if isinstance(decision, dict) else str(decision)
                job.updated_at = datetime.now(timezone.utc)
                session.commit()

    def get_policy_decision(self, job_id: str) -> dict[str, Any] | None:
        with Session(self.engine) as session:
            job = session.scalar(select(JobModel).where(JobModel.job_id == job_id))
            if job and job.policy_data:
                try:
                    return json.loads(job.policy_data)
                except Exception:
                    return None
            return None

    def set_repository_policy(self, repository: str, policy: dict[str, Any]) -> None:
        canonical_repo = repository.strip().lower()
        policy_str = json.dumps(policy)
        now = datetime.now(timezone.utc)
        with Session(self.engine) as session:
            stmt = select(RepositoryPolicyModel).where(
                RepositoryPolicyModel.repository == canonical_repo
            )
            existing = session.scalar(stmt)
            if existing:
                existing.policy_data = policy_str
                existing.updated_at = now
            else:
                new_policy = RepositoryPolicyModel(
                    repository=canonical_repo,
                    policy_data=policy_str,
                    created_at=now,
                    updated_at=now,
                )
                session.add(new_policy)
            session.commit()

    def get_repository_policy(self, repository: str) -> dict[str, Any] | None:
        canonical_repo = repository.strip().lower()
        with Session(self.engine) as session:
            stmt = select(RepositoryPolicyModel).where(
                RepositoryPolicyModel.repository == canonical_repo
            )
            model = session.scalar(stmt)
            if model and model.policy_data:
                try:
                    return json.loads(model.policy_data)
                except Exception:
                    return None
            return None

    def record_transition(self, job_id: str, from_state: str | None, to_state: str, message: str = ""):
        with Session(self.engine) as session:
            job = session.scalar(select(JobModel).where(JobModel.job_id == job_id))
            if not job:
                raise KeyError(job_id)
            job.state = to_state
            job.updated_at = datetime.now(timezone.utc)
            if to_state == "failed" and message:
                job.error = message
            session.add(JobEventModel(
                job_id=job_id,
                from_state=from_state,
                to_state=to_state,
                message=message,
                created_at=datetime.now(timezone.utc),
            ))
            session.commit()

    def save_pr(self, job_id: str, pr: dict[str, Any]) -> None:
        with Session(self.engine) as session:
            job = session.scalar(select(JobModel).where(JobModel.job_id == job_id))
            if job:
                job.pr_data = json.dumps(pr) if isinstance(pr, dict) else str(pr)
                if isinstance(pr, dict):
                    job.pr_number = pr.get("number")
                    job.pr_url = pr.get("url") or pr.get("html_url")
                    job.remediation_branch = pr.get("branch") or pr.get("head_branch")
                    if pr.get("head_sha"):
                        job.current_head_sha = pr.get("head_sha")
                        job.verified_sha = pr.get("head_sha")
                job.updated_at = datetime.now(timezone.utc)
                session.commit()

    def get_pr(self, job_id: str) -> dict[str, Any] | None:
        with Session(self.engine) as session:
            job = session.scalar(select(JobModel).where(JobModel.job_id == job_id))
            if job and job.pr_data:
                try:
                    return json.loads(job.pr_data)
                except Exception:
                    return None
            return None

    def find_by_pr(self, repository: str, pr_number: int) -> StoredJob | None:
        with Session(self.engine) as session:
            job = session.scalar(
                select(JobModel).where(
                    JobModel.repository == repository,
                    JobModel.pr_number == pr_number,
                )
            )
            if not job:
                # Fallback scan pr_data
                all_jobs = session.scalars(
                    select(JobModel).where(JobModel.repository == repository)
                ).all()
                for j in all_jobs:
                    if j.pr_data:
                        try:
                            d = json.loads(j.pr_data)
                            if isinstance(d, dict) and d.get("number") == pr_number:
                                job = j
                                break
                        except Exception:
                            pass
            if not job:
                return None
            return self._to_stored_job(job)

    def find_by_branch(self, repository: str, branch: str) -> StoredJob | None:
        with Session(self.engine) as session:
            job = session.scalar(
                select(JobModel).where(
                    JobModel.repository == repository,
                    JobModel.remediation_branch == branch,
                )
            )
            if not job:
                all_jobs = session.scalars(
                    select(JobModel).where(JobModel.repository == repository)
                ).all()
                for j in all_jobs:
                    if j.remediation_branch == branch or j.target_branch == branch:
                        job = j
                        break
                    if j.pr_data:
                        try:
                            d = json.loads(j.pr_data)
                            if isinstance(d, dict) and (d.get("branch") == branch or d.get("head_branch") == branch):
                                job = j
                                break
                        except Exception:
                            pass
            if not job:
                return None
            return self._to_stored_job(job)

    def find_latest_for_repo(self, repository: str) -> StoredJob | None:
        with Session(self.engine) as session:
            job = session.scalar(
                select(JobModel)
                .where(JobModel.repository == repository)
                .order_by(JobModel.id.desc())
            )
            return self._to_stored_job(job) if job else None

    def mark_stale(self, job_id: str, reason: str = "New commits detected on branch", new_sha: str | None = None) -> None:
        with Session(self.engine) as session:
            job = session.scalar(select(JobModel).where(JobModel.job_id == job_id))
            if job:
                job.is_stale = True
                if new_sha:
                    job.current_head_sha = new_sha
                job.updated_at = datetime.now(timezone.utc)
                session.commit()

    def mark_merged(self, job_id: str, merge_commit_sha: str) -> None:
        with Session(self.engine) as session:
            job = session.scalar(select(JobModel).where(JobModel.job_id == job_id))
            if job:
                job.merge_commit_sha = merge_commit_sha
                job.is_stale = False
                job.updated_at = datetime.now(timezone.utc)
                session.commit()

    def mark_rolled_back(self, job_id: str, reason: str, invalidated_by_sha: str | None = None) -> None:
        with Session(self.engine) as session:
            job = session.scalar(select(JobModel).where(JobModel.job_id == job_id))
            if job:
                job.is_stale = True
                job.invalidation_reason = reason
                job.invalidated_by_sha = invalidated_by_sha
                job.updated_at = datetime.now(timezone.utc)
                session.commit()

    def mark_superseded(self, job_id: str, reason: str, superseded_by_sha: str | None = None) -> None:
        with Session(self.engine) as session:
            job = session.scalar(select(JobModel).where(JobModel.job_id == job_id))
            if job:
                job.is_stale = True
                job.invalidation_reason = reason
                job.invalidated_by_sha = superseded_by_sha
                job.updated_at = datetime.now(timezone.utc)
                session.commit()

    def save_evidence(self, job_id: str, evidence: dict[str, Any]) -> None:
        with Session(self.engine) as session:
            job = session.scalar(select(JobModel).where(JobModel.job_id == job_id))
            if job:
                job.evidence_data = json.dumps(evidence) if isinstance(evidence, dict) else str(evidence)
                if isinstance(evidence, dict) and evidence.get("commit_sha"):
                    job.verified_sha = evidence.get("commit_sha")
                    job.is_stale = False
                job.updated_at = datetime.now(timezone.utc)
                session.commit()

    def get_evidence(self, job_id: str) -> dict[str, Any] | None:
        with Session(self.engine) as session:
            job = session.scalar(select(JobModel).where(JobModel.job_id == job_id))
            if job and job.evidence_data:
                try:
                    return json.loads(job.evidence_data)
                except Exception:
                    return None
            return None

    def get_events(self, job_id: str) -> list[dict[str, Any]]:
        with Session(self.engine) as session:
            events = session.scalars(
                select(JobEventModel)
                .where(JobEventModel.job_id == job_id)
                .order_by(JobEventModel.id.asc())
            ).all()
            return [
                {
                    "id": e.id,
                    "from_state": e.from_state,
                    "to_state": e.to_state,
                    "message": e.message,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in events
            ]

    def get_state(self, job_id: str) -> str | None:
        with Session(self.engine) as session:
            job = session.scalar(select(JobModel).where(JobModel.job_id == job_id))
            return None if job is None else job.state

    def _to_stored_job(self, job: JobModel) -> StoredJob:
        return StoredJob(
            job_id=job.job_id,
            delivery_id=job.delivery_id,
            repository=job.repository,
            commit_sha=job.commit_sha,
            event_type=job.event_type,
            state=job.state,
            error=job.error,
            pr_data=job.pr_data,
            evidence_data=job.evidence_data,
            policy_data=job.policy_data,
            created_at=job.created_at,
            updated_at=job.updated_at,
            installation_id=job.installation_id,
            check_run_id=job.check_run_id,
            target_branch=job.target_branch,
            pr_number=job.pr_number,
            pr_url=job.pr_url,
            remediation_branch=job.remediation_branch,
            current_head_sha=job.current_head_sha,
            verified_sha=job.verified_sha,
            merge_commit_sha=job.merge_commit_sha,
            is_stale=bool(job.is_stale),
            invalidation_reason=job.invalidation_reason,
            invalidated_by_sha=job.invalidated_by_sha,
        )

    def get(self, job_id: str) -> StoredJob | None:
        with Session(self.engine) as session:
            job = session.scalar(select(JobModel).where(JobModel.job_id == job_id))
            if not job:
                return None
            return self._to_stored_job(job)

    def update(self, job) -> None:
        with Session(self.engine) as session:
            job_id = getattr(job, "job_id", None) or getattr(job, "id", None)
            if not job_id:
                return
            db_job = session.scalar(select(JobModel).where(JobModel.job_id == str(job_id)))
            if db_job:
                state_val = getattr(job, "state", db_job.state)
                if hasattr(state_val, "value"):
                    state_val = state_val.value
                db_job.state = str(state_val)
                if getattr(job, "error", None) is not None:
                    db_job.error = str(job.error)
                if getattr(job, "check_run_id", None) is not None:
                    db_job.check_run_id = job.check_run_id
                if getattr(job, "target_branch", None) is not None:
                    db_job.target_branch = job.target_branch
                if getattr(job, "pr_number", None) is not None:
                    db_job.pr_number = job.pr_number
                if getattr(job, "pr_url", None) is not None:
                    db_job.pr_url = job.pr_url
                if getattr(job, "remediation_branch", None) is not None:
                    db_job.remediation_branch = job.remediation_branch
                if getattr(job, "current_head_sha", None) is not None:
                    db_job.current_head_sha = job.current_head_sha
                if getattr(job, "verified_sha", None) is not None:
                    db_job.verified_sha = job.verified_sha
                if getattr(job, "merge_commit_sha", None) is not None:
                    db_job.merge_commit_sha = job.merge_commit_sha
                if getattr(job, "is_stale", None) is not None:
                    db_job.is_stale = job.is_stale
                if getattr(job, "invalidation_reason", None) is not None:
                    db_job.invalidation_reason = job.invalidation_reason
                if getattr(job, "invalidated_by_sha", None) is not None:
                    db_job.invalidated_by_sha = job.invalidated_by_sha
                if getattr(job, "policy_decision", None) is not None:
                    p = job.policy_decision
                    db_job.policy_data = json.dumps(p) if isinstance(p, dict) else str(p)
                db_job.updated_at = datetime.now(timezone.utc)
                session.commit()

    def all(self) -> list[StoredJob]:
        with Session(self.engine) as session:
            jobs = session.scalars(select(JobModel).order_by(JobModel.id.desc())).all()
            return [self._to_stored_job(j) for j in jobs]

    def list_jobs(
        self,
        repository: str | None = None,
        state: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[StoredJob]:
        with Session(self.engine) as session:
            stmt = select(JobModel).order_by(JobModel.id.desc())
            if repository:
                stmt = stmt.where(JobModel.repository == repository)
            if state:
                stmt = stmt.where(JobModel.state == state.lower())
            if offset:
                stmt = stmt.offset(offset)
            if limit:
                stmt = stmt.limit(limit)
            jobs = session.scalars(stmt).all()
            return [self._to_stored_job(j) for j in jobs]

    def count_jobs(
        self,
        repository: str | None = None,
        state: str | None = None,
    ) -> int:
        from sqlalchemy import func
        with Session(self.engine) as session:
            stmt = select(func.count(JobModel.id))
            if repository:
                stmt = stmt.where(JobModel.repository == repository)
            if state:
                stmt = stmt.where(JobModel.state == state.lower())
            return session.scalar(stmt) or 0

    def onboard_repository(
        self,
        repository: str,
        default_branch: str = "main",
        installation_id: int | None = None,
        status: str = "active",
        provider: str = "github",
    ) -> dict[str, Any]:
        clean_repo = repository.strip()
        parts = clean_repo.split("/", 1)
        owner = parts[0] if len(parts) > 1 else ""
        name = parts[1] if len(parts) > 1 else clean_repo

        with Session(self.engine) as session:
            existing = session.scalar(select(RepositoryModel).where(RepositoryModel.repository == clean_repo))
            now = datetime.now(timezone.utc)
            if existing:
                existing.default_branch = default_branch
                if installation_id is not None:
                    existing.installation_id = installation_id
                existing.status = status
                existing.provider = provider
                existing.updated_at = now
                session.commit()
                return {
                    "id": existing.id,
                    "repository": existing.repository,
                    "owner": existing.owner,
                    "name": existing.name,
                    "provider": existing.provider,
                    "default_branch": existing.default_branch,
                    "installation_id": existing.installation_id,
                    "status": existing.status,
                    "created_at": existing.created_at.isoformat() if existing.created_at else None,
                    "updated_at": existing.updated_at.isoformat() if existing.updated_at else None,
                }
            else:
                new_repo = RepositoryModel(
                    repository=clean_repo,
                    owner=owner,
                    name=name,
                    provider=provider,
                    default_branch=default_branch,
                    installation_id=installation_id,
                    status=status,
                    created_at=now,
                    updated_at=now,
                )
                session.add(new_repo)
                session.commit()
                return {
                    "id": new_repo.id,
                    "repository": new_repo.repository,
                    "owner": new_repo.owner,
                    "name": new_repo.name,
                    "provider": new_repo.provider,
                    "default_branch": new_repo.default_branch,
                    "installation_id": new_repo.installation_id,
                    "status": new_repo.status,
                    "created_at": new_repo.created_at.isoformat() if new_repo.created_at else None,
                    "updated_at": new_repo.updated_at.isoformat() if new_repo.updated_at else None,
                }

    def get_repository(self, repository: str) -> dict[str, Any] | None:
        clean_repo = repository.strip()
        with Session(self.engine) as session:
            repo = session.scalar(select(RepositoryModel).where(RepositoryModel.repository == clean_repo))
            if not repo:
                return None
            return {
                "id": repo.id,
                "repository": repo.repository,
                "owner": repo.owner,
                "name": repo.name,
                "provider": repo.provider,
                "default_branch": repo.default_branch,
                "installation_id": repo.installation_id,
                "status": repo.status,
                "created_at": repo.created_at.isoformat() if repo.created_at else None,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
            }

    def list_repositories(self) -> list[dict[str, Any]]:
        with Session(self.engine) as session:
            # 1. Fetch registered repositories
            registered_repos = session.scalars(select(RepositoryModel).order_by(RepositoryModel.id.desc())).all()
            repos: dict[str, dict[str, Any]] = {}

            for reg in registered_repos:
                repos[reg.repository] = {
                    "repository": reg.repository,
                    "installation_status": "installed" if reg.status == "active" else reg.status,
                    "total_jobs": 0,
                    "active_jobs": 0,
                    "verified_prs": 0,
                    "failed_jobs": 0,
                    "last_job_id": None,
                    "last_activity": reg.created_at.isoformat() if reg.created_at else None,
                }

            # 2. Accumulate metrics from jobs
            jobs = session.scalars(select(JobModel).order_by(JobModel.id.desc())).all()
            for j in jobs:
                repo_name = j.repository
                if not repo_name:
                    continue
                if repo_name not in repos:
                    repos[repo_name] = {
                        "repository": repo_name,
                        "installation_status": "installed",
                        "total_jobs": 0,
                        "active_jobs": 0,
                        "verified_prs": 0,
                        "failed_jobs": 0,
                        "last_job_id": None,
                        "last_activity": None,
                    }
                r = repos[repo_name]
                r["total_jobs"] += 1
                state_val = (j.state or "").lower()
                if state_val in {"queued", "scanning", "analyzing", "patching", "verifying"}:
                    r["active_jobs"] += 1
                elif state_val in {"verified", "pr_created", "pr_updated", "pr_merged"}:
                    r["verified_prs"] += 1
                elif state_val == "failed":
                    r["failed_jobs"] += 1

                created_at = j.created_at
                if created_at:
                    c_iso = created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at)
                    if not r["last_activity"] or c_iso > r["last_activity"]:
                        r["last_activity"] = c_iso
                        r["last_job_id"] = j.job_id

            return sorted(list(repos.values()), key=lambda x: x.get("last_activity") or "", reverse=True)

