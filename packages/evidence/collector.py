from __future__ import annotations
from hashlib import sha256

from packages.evidence.models import EvidenceBundle


def build_evidence(
    *,
    job_id,
    commit_sha,
    patch_diff,
    scanner_summary,
    test_summary,
    verification_summary,
):
    bundle = EvidenceBundle(
        job_id=job_id,
        commit_sha=commit_sha,
        patch_sha256=sha256(patch_diff.encode()).hexdigest(),
        scanner_summary=scanner_summary,
        test_summary=test_summary,
        verification_summary=verification_summary,
    )
    bundle.validate()
    return bundle
