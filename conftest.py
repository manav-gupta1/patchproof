import pytest
from pathlib import Path

def pytest_ignore_collect(collection_path, config):
    path = Path(str(collection_path))
    return "historical" in path.parts or "fixtures" in path.parts



@pytest.fixture(autouse=True)
def _cleanup_named_result_race_db():
    yield
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(
            "sqlite:///file:result_race?mode=memory&cache=shared&uri=true",
            connect_args={"check_same_thread": False},
        )
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS jobs"))
        engine.dispose()
    except Exception:
        pass
