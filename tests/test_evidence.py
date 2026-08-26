import pytest
from sqlalchemy import create_engine

from packages.evidence.collector import build_evidence
from packages.evidence.store import EvidenceStore
from packages.evidence.models import EvidenceBundle


def bundle(job="job-1", diff="same"):
    return build_evidence(
        job_id=job,
        commit_sha="a" * 40,
        patch_diff=diff,
        scanner_summary="0 findings",
        test_summary="42 tests passed",
        verification_summary="verification passed",
    )


def test_evidence_is_canonical_and_hashed():
    one = bundle()
    two = bundle()
    assert one.evidence_sha256 == two.evidence_sha256
    assert len(one.evidence_sha256) == 64


def test_evidence_store_is_idempotent():
    engine = create_engine("sqlite://")
    store = EvidenceStore(engine)
    store.create_schema()
    one = bundle()
    first = store.put(one)
    second = store.put(one)
    assert first.id == second.id
    assert store.get("job-1").evidence_sha256 == one.evidence_sha256


def test_conflicting_evidence_for_same_job_is_rejected():
    engine = create_engine("sqlite://")
    store = EvidenceStore(engine)
    store.create_schema()
    store.put(bundle(diff="first"))
    with pytest.raises(ValueError):
        store.put(bundle(diff="different"))


def test_invalid_evidence_rejected():
    with pytest.raises(ValueError):
        EvidenceBundle(
            job_id="job-1",
            commit_sha="bad",
            patch_sha256="0" * 64,
            scanner_summary="x",
            test_summary="x",
            verification_summary="x",
        ).validate()
