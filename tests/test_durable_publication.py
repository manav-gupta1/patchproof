from types import SimpleNamespace
from sqlalchemy import create_engine

from packages.github.durable_store import DurablePublicationRecordStore
from packages.github.recovery import PublicationRecoveryWorker
from packages.github.transaction import PublicationPhase, PublicationRecord


class Evidence:
    evidence_sha256 = "e" * 64


class GitHub:
    def __init__(self):
        self.calls = 0
    def publish(self, **kwargs):
        self.calls += 1
        return {"number": 9, "url": "https://github.example/pr/9"}


def test_publication_record_survives_store_recreation():
    engine = create_engine("sqlite://")
    store = DurablePublicationRecordStore(engine)
    store.create_schema()
    record = PublicationRecord(
        job_id="job-restart",
        evidence_sha256="e"*64,
        branch="patchproof/job-restart",
        commit_sha="c"*40,
        phase=PublicationPhase.BRANCH_PUSHED,
    )
    store.put(record)

    restarted = DurablePublicationRecordStore(engine)
    loaded = restarted.get("job-restart")
    assert loaded == record


def test_recovery_completes_durable_transaction_after_restart():
    engine = create_engine("sqlite://")
    store = DurablePublicationRecordStore(engine)
    store.create_schema()
    store.put(PublicationRecord(
        job_id="job-recover",
        evidence_sha256="e"*64,
        branch="patchproof/job-recover",
        commit_sha="c"*40,
        phase=PublicationPhase.BRANCH_PUSHED,
    ))

    github = GitHub()
    recovered = PublicationRecoveryWorker(store, github).recover(
        job=SimpleNamespace(job_id="job-recover"),
        evidence=Evidence(),
        title="x", body="x",
        head="patchproof/job-recover", base="main",
    )

    assert recovered.phase == PublicationPhase.PR_CREATED
    assert store.get("job-recover").phase == PublicationPhase.PR_CREATED
    assert github.calls == 1


def test_recovery_is_evidence_bound():
    engine = create_engine("sqlite://")
    store = DurablePublicationRecordStore(engine)
    store.create_schema()
    store.put(PublicationRecord(
        job_id="job-bound",
        evidence_sha256="a"*64,
        branch="patchproof/job-bound",
        commit_sha="c"*40,
        phase=PublicationPhase.BRANCH_PUSHED,
    ))

    class Different:
        evidence_sha256 = "b"*64

    try:
        PublicationRecoveryWorker(store, GitHub()).recover(
            job=SimpleNamespace(job_id="job-bound"),
            evidence=Different(), title="x", body="x",
            head="patchproof/job-bound", base="main",
        )
        assert False
    except RuntimeError as exc:
        assert "evidence" in str(exc)
