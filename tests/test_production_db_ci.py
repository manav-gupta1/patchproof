import os
import pytest
from sqlalchemy import create_engine

from packages.jobs.sql_store import SQLJobStore


DB_URL_ENV = "PATCHPROOF_DATABASE_URL"


def production_url():
    return os.getenv(DB_URL_ENV)


@pytest.mark.integration
def test_configured_production_database_schema_and_store():
    url=production_url()
    if not url:
        pytest.skip(f"{DB_URL_ENV} is not configured")

    engine=create_engine(url)
    store=SQLJobStore(engine)
    store.create_schema()

    job_id=store.create("production-db-ci")
    assert store.get(job_id) is not None


@pytest.mark.integration
def test_configured_production_database_supports_transaction_boundary():
    url=production_url()
    if not url:
        pytest.skip(f"{DB_URL_ENV} is not configured")

    engine=create_engine(url)
    store=SQLJobStore(engine)
    store.create_schema()

    job_id=store.create("transaction-boundary")
    with engine.begin() as conn:
        row=conn.execute(
            store.jobs.select().where(store.jobs.c.job_id == job_id)
        ).first()

    assert row is not None
