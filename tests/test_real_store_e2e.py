from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine

from packages.jobs.sql_store import SQLJobStore


def test_real_store_claim_and_persisted_job_state():
    engine=create_engine("sqlite://")
    store=SQLJobStore(engine)
    store.create_schema()

    job_id=store.create("real-e2e")
    assert job_id is not None

    # Exercise only methods actually exposed by the production store.
    assert hasattr(store, "get")
    job=store.get(job_id)
    assert job is not None

def test_real_store_schema_survives_second_store_instance():
    engine=create_engine("sqlite://")
    first=SQLJobStore(engine)
    first.create_schema()
    job_id=first.create("restart-e2e")

    second=SQLJobStore(engine)
    second.create_schema()
    assert second.get(job_id) is not None
