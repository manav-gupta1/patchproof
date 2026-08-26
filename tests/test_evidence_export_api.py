from __future__ import annotations

import json
from fastapi.testclient import TestClient

from packages.api.app import create_app
from packages.auth import ApiKeyStore, TenantContext
from packages.jobs.state import JobRecord, JobState
from packages.jobs.store import InMemoryJobStore
from packages.signing import Ed25519EvidenceSigner, verify_evidence
from packages.webhooks.handlers import WebhookDispatcher


def test_export_evidence_bundle_and_verify_signature():
    store = InMemoryJobStore()
    api_key_store = ApiKeyStore()
    api_key_store.register_token(
        "tenant_token",
        TenantContext(tenant_id="tenant-1", name="Acme Corp", allowed_repositories=("acme/app",)),
    )

    dispatcher = WebhookDispatcher(jobs=store, enqueue=lambda j: None)
    app = create_app(
        dispatcher=dispatcher,
        store=store,
        api_key_store=api_key_store,
        auth_enabled=True,
        webhook_secret="test-secret",
    )
    client = TestClient(app)

    job_id = "job-export-test-1"
    job = JobRecord(
        job_id=job_id,
        repository="acme/app",
        delivery_id="deliv-export-1",
        commit_sha="a" * 40,
        state=JobState.VERIFIED,
    )
    store.create(job)

    signer = Ed25519EvidenceSigner()
    evidence_payload = {
        "job_id": job_id,
        "commit_sha": "a" * 40,
        "repository": "acme/app",
        "verified": True,
        "finding_count": 1,
        "target_finding": {
            "rule_id": "python.lang.security.deserialization.pickle",
            "fingerprint": "fp-pickle-1",
            "severity": "CRITICAL",
        },
        "verification_results": {
            "verification_status": "passed",
            "target_vulnerability_eliminated": True,
            "rescan_findings_count": 0,
            "test_summary": "1 passed in 0.05s",
        },
    }
    signed_bundle = signer.sign(evidence_payload)
    store.save_evidence(job_id, signed_bundle)

    # 1. Export evidence bundle as JSON attachment
    resp = client.get(
        f"/jobs/{job_id}/evidence/export",
        headers={"Authorization": "Bearer tenant_token"},
    )
    assert resp.status_code == 200
    assert "application/json" in resp.headers["content-type"]
    assert f'attachment; filename="patchproof-evidence-{job_id}.json"' in resp.headers["content-disposition"]

    exported_json = resp.json()
    assert exported_json["job_id"] == job_id
    assert exported_json["verified"] is True
    assert exported_json["signature"] is not None
    assert exported_json["sha256_digest"] is not None

    # 2. Verify digital signature on exported payload
    from packages.signing.keys import PublicKeyStore
    store_keys = PublicKeyStore()
    store_keys.register_key(signer.key_id, signer.public_key)
    res = verify_evidence(exported_json, key_store=store_keys)
    assert res.valid is True


def test_export_evidence_bundle_tenant_isolation():
    store = InMemoryJobStore()
    api_key_store = ApiKeyStore()
    api_key_store.register_token(
        "tenant_other_token",
        TenantContext(tenant_id="tenant-other", name="Other Corp", allowed_repositories=("other/repo",)),
    )

    dispatcher = WebhookDispatcher(jobs=store, enqueue=lambda j: None)
    app = create_app(
        dispatcher=dispatcher,
        store=store,
        api_key_store=api_key_store,
        auth_enabled=True,
        webhook_secret="test-secret",
    )
    client = TestClient(app)

    job_id = "job-private-1"
    job = JobRecord(
        job_id=job_id,
        repository="confidential/repo",
        delivery_id="deliv-priv-1",
        commit_sha="c" * 40,
        state=JobState.VERIFIED,
    )
    store.create(job)
    store.save_evidence(job_id, {"verified": True, "commit_sha": "c" * 40})

    resp = client.get(
        f"/jobs/{job_id}/evidence/export",
        headers={"Authorization": "Bearer tenant_other_token"},
    )
    assert resp.status_code == 403
    assert "not authorized" in resp.json()["detail"]
