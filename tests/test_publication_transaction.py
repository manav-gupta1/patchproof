from types import SimpleNamespace
import pytest

from packages.github.transaction import (
    PublicationPhase, PublicationRecord,
    PublicationTransaction, PublicationTransactionError,
)
from packages.github.transaction_store import InMemoryPublicationRecordStore


class Evidence:
    evidence_sha256 = "e" * 64


class Git:
    def __init__(self):
        self.calls = 0

    def create_and_push(self, head, base, patch_diff):
        self.calls += 1
        return "c" * 40


class GitHub:
    def __init__(self):
        self.calls = 0
        self.crash_once = False

    def publish(self, **kwargs):
        self.calls += 1
        if self.crash_once:
            self.crash_once = False
            raise RuntimeError("simulated worker crash")
        return {"number": 17, "url": "https://github.example/pr/17"}


def make():
    return (
        InMemoryPublicationRecordStore(),
        Git(),
        GitHub(),
        SimpleNamespace(job_id="job-1"),
    )


def test_push_is_persisted_before_pr_creation():
    store, git, github, job = make()
    tx = PublicationTransaction(store, git, github)
    record = tx.publish(
        job=job, evidence=Evidence(), patch_diff="diff",
        title="x", body="x", head="patchproof/job-1", base="main"
    )
    assert record.phase == PublicationPhase.PR_CREATED
    assert git.calls == 1
    assert github.calls == 1
    assert store.get(job.job_id).commit_sha == "c" * 40


def test_crash_after_push_resumes_without_second_push():
    store, git, github, job = make()
    github.crash_once = True
    tx = PublicationTransaction(store, git, github)

    with pytest.raises(RuntimeError):
        tx.publish(
            job=job, evidence=Evidence(), patch_diff="diff",
            title="x", body="x", head="patchproof/job-1", base="main"
        )

    assert store.get(job.job_id).phase == PublicationPhase.BRANCH_PUSHED
    assert git.calls == 1

    record = tx.publish(
        job=job, evidence=Evidence(), patch_diff="diff",
        title="x", body="x", head="patchproof/job-1", base="main"
    )
    assert record.phase == PublicationPhase.PR_CREATED
    assert git.calls == 1
    assert github.calls == 2


def test_different_evidence_cannot_resume_old_transaction():
    store, git, github, job = make()
    store.put(PublicationRecord(
        job_id=job.job_id, evidence_sha256="a"*64,
        branch="patchproof/job-1", commit_sha="c"*40,
        phase=PublicationPhase.BRANCH_PUSHED,
    ))

    class Different:
        evidence_sha256 = "b" * 64

    tx = PublicationTransaction(store, git, github)
    with pytest.raises(PublicationTransactionError):
        tx.publish(
            job=job, evidence=Different(), patch_diff="diff",
            title="x", body="x", head="patchproof/job-1", base="main"
        )
