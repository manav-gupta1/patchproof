from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_schema_contract():
    sql=(ROOT/"packages/persistence/schema.sql").read_text()
    for table in ["jobs","state_transitions","evidence","patches","verification_runs","pull_requests"]:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in sql
    assert "UNIQUE(job_id, sha256)" in sql
    assert "version BIGINT NOT NULL DEFAULT 0" in sql
    assert "REFERENCES jobs(job_id)" in sql

def test_repository_concurrency_contract():
    code=(ROOT/"packages/persistence/repository.py").read_text()
    assert "FOR UPDATE" in code
    assert "version=version+1" in code
    assert "optimistic concurrency conflict" in code
