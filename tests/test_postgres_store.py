from packages.store.postgres import PostgresJobStore


def test_postgres_store_sqlite_compatibility(tmp_path):
    db = tmp_path / "jobs.db"
    store = PostgresJobStore(f"sqlite:///{db}")
    store.create_schema()

    job = store.create_from_webhook(
        delivery_id="d1",
        repository="acme/staging",
        commit_sha="a" * 40,
        event_type="code_scanning_alert",
    )
    assert job.job_id == "job-d1"
    assert store.exists_delivery("d1")

    duplicate = store.create_from_webhook(
        delivery_id="d1",
        repository="acme/staging",
        commit_sha="b" * 40,
        event_type="code_scanning_alert",
    )
    assert duplicate.job_id == job.job_id
    assert store.get_state(job.job_id) == "queued"

    store.record_transition(job.job_id, "queued", "scanning", "worker started")
    assert store.get_state(job.job_id) == "scanning"
