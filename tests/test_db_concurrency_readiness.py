import inspect
from sqlalchemy import create_engine

from packages.jobs.sql_store import SQLJobStore


def test_store_uses_transactional_sqlalchemy_engine():
    engine=create_engine("sqlite://")
    store=SQLJobStore(engine)
    store.create_schema()

    assert store.engine is engine
    assert hasattr(store, "jobs")

    source=inspect.getsource(SQLJobStore)
    assert "engine.begin()" in source


def test_store_schema_is_created_by_real_store():
    engine=create_engine("sqlite://")
    store=SQLJobStore(engine)
    store.create_schema()

    with engine.connect() as conn:
        tables=conn.exec_driver_sql(
            "select name from sqlite_master where type='table'"
        ).fetchall()

    names={row[0] for row in tables}
    assert store.jobs.name in names
