from pathlib import Path
import inspect
import pytest

from packages.jobs.sql_store import SQLJobStore


def test_production_sql_store_is_the_system_under_test():
    # Guard against accidentally validating only the test harness.
    assert SQLJobStore.__module__ == "packages.jobs.sql_store"
    assert hasattr(SQLJobStore, "create_schema")
    assert hasattr(SQLJobStore, "create")


def test_production_sql_store_schema_can_be_initialized():
    from sqlalchemy import create_engine
    engine=create_engine("sqlite://")
    store=SQLJobStore(engine)
    store.create_schema()
    assert inspect.isclass(SQLJobStore)
    assert hasattr(store, "jobs")
    assert store.jobs is not None
