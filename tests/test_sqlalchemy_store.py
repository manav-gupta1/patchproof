import pytest

sqlalchemy = pytest.importorskip("sqlalchemy")

from packages.jobs.sqlalchemy_store import SQLAlchemyJobStore
from packages.jobs.state import JobRecord, JobState


def test_sqlalchemy_store_round_trip(tmp_path):
    db = tmp_path / "jobs.db"
    store = SQLAlchemyJobStore(f"sqlite:///{db}")
    store.create_tables()

    job = JobRecord("j1", "acme/demo", "d1", "a"*40)
    store.create(job)
    loaded = store.get("j1")

    assert loaded.job_id == job.job_id
    assert loaded.state is JobState.QUEUED

    updated = JobRecord(
        job.job_id, job.repository, job.delivery_id, job.commit_sha,
        state=JobState.QUEUED, created_at=job.created_at,
        updated_at=job.updated_at,
    )
    store.update(updated)
    assert store.get("j1").state is JobState.QUEUED
