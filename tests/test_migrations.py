def test_initial_migration_has_expected_revision():
    from pathlib import Path
    p = Path("alembic/versions/0001_jobs_and_events.py")
    text = p.read_text()
    assert 'revision = "0001_jobs_events"' in text
    assert "op.create_table(" in text
    assert '"jobs"' in text
    assert '"job_events"' in text
