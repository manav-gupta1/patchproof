from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from packages.orchestration.models import JobState, RemediationJob


class PostgresJobStore:
    """PostgreSQL repository contract.

    This implementation uses an injected DB-API connection factory so the
    security-critical transaction boundaries remain explicit and testable.
    """

    def __init__(self, connection_factory) -> None:
        self.connection_factory = connection_factory

    def create_with_idempotency(
        self,
        job: RemediationJob,
        idempotency_key: str,
    ) -> tuple[RemediationJob, bool]:
        with self.connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO remediation_jobs
                    (id, repository, commit_sha, finding_fingerprint, state)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        job.id,
                        job.repository,
                        job.commit_sha,
                        job.finding_fingerprint,
                        job.state.value,
                    ),
                )
                cur.execute(
                    """
                    INSERT INTO job_idempotency_keys (idempotency_key, job_id)
                    VALUES (%s, %s)
                    ON CONFLICT (idempotency_key) DO NOTHING
                    RETURNING job_id
                    """,
                    (idempotency_key, job.id),
                )
                row = cur.fetchone()
                if row is None:
                    cur.execute(
                        """
                        SELECT j.id, j.repository, j.commit_sha,
                               j.finding_fingerprint, j.state, j.attempt,
                               j.failure_code, j.failure_message,
                               j.evidence_id, j.pull_request_url,
                               j.created_at, j.updated_at
                        FROM job_idempotency_keys k
                        JOIN remediation_jobs j ON j.id = k.job_id
                        WHERE k.idempotency_key = %s
                        """,
                        (idempotency_key,),
                    )
                    existing = self._row_to_job(cur.fetchone())
                    conn.commit()
                    return existing, False

                cur.execute(
                    """
                    INSERT INTO job_events
                    (job_id, from_state, to_state, event_type, message)
                    VALUES (%s, NULL, %s, 'created', NULL)
                    """,
                    (job.id, job.state.value),
                )
                conn.commit()
                return job, True

    def claim_ready(
        self,
        worker_id: str,
        lease_seconds: int = 300,
    ) -> RemediationJob | None:
        now = datetime.now(timezone.utc)
        lease_until = now + timedelta(seconds=lease_seconds)

        with self.connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, repository, commit_sha, finding_fingerprint,
                           state, attempt, failure_code, failure_message,
                           evidence_id, pull_request_url, created_at, updated_at
                    FROM remediation_jobs
                    WHERE state IN ('received', 'analyzing', 'exploiting',
                                    'patching', 'verifying')
                      AND (
                        lease_expires_at IS NULL
                        OR lease_expires_at < %s
                      )
                    ORDER BY created_at
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                    """,
                    (now,),
                )
                row = cur.fetchone()
                if row is None:
                    conn.commit()
                    return None

                job = self._row_to_job(row)
                cur.execute(
                    """
                    UPDATE remediation_jobs
                    SET lease_owner = %s,
                        lease_expires_at = %s,
                        attempt = attempt + 1,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (worker_id, lease_until, job.id),
                )
                conn.commit()
                job.attempt += 1
                return job

    def renew_lease(
        self,
        job_id: UUID | str,
        worker_id: str,
        lease_seconds: int = 300,
    ) -> bool:
        lease_until = datetime.now(timezone.utc) + timedelta(seconds=lease_seconds)
        with self.connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE remediation_jobs
                    SET lease_expires_at = %s, updated_at = NOW()
                    WHERE id = %s AND lease_owner = %s
                    """,
                    (lease_until, str(job_id), worker_id),
                )
                changed = cur.rowcount == 1
                conn.commit()
                return changed

    def release_lease(self, job_id: UUID | str, worker_id: str) -> bool:
        with self.connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE remediation_jobs
                    SET lease_owner = NULL, lease_expires_at = NULL,
                        updated_at = NOW()
                    WHERE id = %s AND lease_owner = %s
                    """,
                    (str(job_id), worker_id),
                )
                changed = cur.rowcount == 1
                conn.commit()
                return changed

    def record_event(
        self,
        job_id: UUID | str,
        from_state: str | None,
        to_state: str,
        event_type: str,
        message: str | None = None,
    ) -> None:
        with self.connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO job_events
                    (job_id, from_state, to_state, event_type, message)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        str(job_id),
                        from_state,
                        to_state,
                        event_type,
                        message,
                    ),
                )
                conn.commit()

    @staticmethod
    def _row_to_job(row: Any) -> RemediationJob:
        if row is None:
            raise KeyError("job not found")
        (
            job_id,
            repository,
            commit_sha,
            finding_fingerprint,
            state,
            attempt,
            failure_code,
            failure_message,
            evidence_id,
            pull_request_url,
            created_at,
            updated_at,
        ) = row
        return RemediationJob(
            id=str(job_id),
            state=JobState(state),
            repository=repository,
            commit_sha=commit_sha,
            finding_fingerprint=finding_fingerprint,
            attempt=attempt,
            failure_code=failure_code,
            failure_message=failure_message,
            evidence_id=evidence_id,
            pull_request_url=pull_request_url,
            created_at=created_at,
            updated_at=updated_at,
        )
