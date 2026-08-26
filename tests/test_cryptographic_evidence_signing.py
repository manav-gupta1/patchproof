import json
import binascii
import subprocess
from datetime import datetime, timezone
import pytest
from cryptography.hazmat.primitives.asymmetric import ed25519
from fastapi.testclient import TestClient

from packages.api.app import create_app
from packages.jobs.state import JobRecord, JobState
from packages.jobs.store import InMemoryJobStore
from packages.jobs.pipeline_factory import create_concrete_remediation_orchestrator
from packages.signing import (
    Ed25519EvidenceSigner,
    Ed25519EvidenceVerifier,
    PublicKeyStore,
    canonicalize_evidence,
    compute_evidence_digest,
    verify_evidence,
)
from packages.webhooks.handlers import WebhookDispatcher


@pytest.fixture
def sample_evidence():
    return {
        "evidence_id": "ev-sample-001",
        "job_id": "job-sample-001",
        "commit_sha": "a" * 40,
        "repository": "example/test-repo",
        "verified": True,
        "finding_count": 1,
        "target_finding": {
            "rule_id": "python.sql-injection",
            "fingerprint": "fp-sqli-12345",
            "severity": "HIGH",
        },
        "verification_results": {
            "rescan_findings_count": 0,
            "target_vulnerability_eliminated": True,
            "verification_status": "passed",
            "test_summary": "Clean re-scan completed.",
        },
        "patch_summary": {
            "title": "fix(security): parameterize SQL query",
            "files_changed": ["app.py"],
            "head_branch": "patchproof/fix-sqli",
            "base_branch": "main",
            "explanation": "Replaced f-string query with parameterized query.",
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def test_deterministic_canonicalization(sample_evidence):
    """Test that key ordering does not affect the canonical byte representation or digest."""
    # Reverse dictionary keys
    rev_evidence = dict(reversed(list(sample_evidence.items())))

    canonical1 = canonicalize_evidence(sample_evidence)
    canonical2 = canonicalize_evidence(rev_evidence)
    assert canonical1 == canonical2

    digest1 = compute_evidence_digest(sample_evidence)
    digest2 = compute_evidence_digest(rev_evidence)
    assert digest1 == digest2


def test_valid_signature_creation_and_verification(sample_evidence):
    """Test signing evidence and successfully verifying the resulting signed bundle."""
    priv_key = ed25519.Ed25519PrivateKey.generate()
    pub_key = priv_key.public_key()
    key_id = "test-key-alpha"

    signer = Ed25519EvidenceSigner(private_key=priv_key, key_id=key_id)
    signed = signer.sign(sample_evidence)

    assert "sha256_digest" in signed
    assert "signature" in signed
    assert signed["signing_algorithm"] == "ed25519"
    assert signed["signing_key_id"] == key_id
    assert "signed_at" in signed

    key_store = PublicKeyStore()
    key_store.register_key(key_id, pub_key)

    verifier = Ed25519EvidenceVerifier(key_store=key_store)
    res = verifier.verify(signed)

    assert res.valid is True
    assert res.key_id == key_id
    assert res.signing_algorithm == "ed25519"
    assert res.sha256_digest == signed["sha256_digest"]
    assert res.error is None


def test_tampered_evidence_payload_rejected(sample_evidence):
    """Test that any modification to the signed evidence payload fails verification."""
    priv_key = ed25519.Ed25519PrivateKey.generate()
    pub_key = priv_key.public_key()
    key_id = "test-key-tamper"

    signer = Ed25519EvidenceSigner(private_key=priv_key, key_id=key_id)
    signed = signer.sign(sample_evidence)

    key_store = PublicKeyStore()
    key_store.register_key(key_id, pub_key)
    verifier = Ed25519EvidenceVerifier(key_store=key_store)

    # Tamper with verified boolean
    tampered = dict(signed)
    tampered["verified"] = False

    res = verifier.verify(tampered)
    assert res.valid is False
    assert "tampered" in res.error.lower()


def test_tampered_digest_rejected(sample_evidence):
    """Test that modifying sha256_digest directly fails verification."""
    priv_key = ed25519.Ed25519PrivateKey.generate()
    pub_key = priv_key.public_key()
    key_id = "test-key-digest-tamper"

    signer = Ed25519EvidenceSigner(private_key=priv_key, key_id=key_id)
    signed = signer.sign(sample_evidence)

    key_store = PublicKeyStore()
    key_store.register_key(key_id, pub_key)
    verifier = Ed25519EvidenceVerifier(key_store=key_store)

    tampered = dict(signed)
    tampered["sha256_digest"] = "0" * 64

    res = verifier.verify(tampered)
    assert res.valid is False
    assert "tampered" in res.error.lower()


def test_wrong_public_key_rejected(sample_evidence):
    """Test that verifying against a different public key fails with signature mismatch."""
    priv_key1 = ed25519.Ed25519PrivateKey.generate()
    priv_key2 = ed25519.Ed25519PrivateKey.generate()
    key_id = "test-key-wrong"

    signer = Ed25519EvidenceSigner(private_key=priv_key1, key_id=key_id)
    signed = signer.sign(sample_evidence)

    # Register wrong public key under same key_id
    key_store = PublicKeyStore()
    key_store.register_key(key_id, priv_key2.public_key())
    verifier = Ed25519EvidenceVerifier(key_store=key_store)

    res = verifier.verify(signed)
    assert res.valid is False
    assert "signature mismatch" in res.error.lower()


def test_unknown_signing_key_id_rejected(sample_evidence):
    """Test that evidence signed with an unknown key ID is rejected."""
    priv_key = ed25519.Ed25519PrivateKey.generate()
    signer = Ed25519EvidenceSigner(private_key=priv_key, key_id="unknown-key-999")
    signed = signer.sign(sample_evidence)

    key_store = PublicKeyStore()
    verifier = Ed25519EvidenceVerifier(key_store=key_store)

    res = verifier.verify(signed)
    assert res.valid is False
    assert "not registered" in res.error.lower()


def test_private_key_never_exposed_in_repr():
    """Test that Ed25519EvidenceSigner repr and str do not leak raw private key bytes."""
    priv_key = ed25519.Ed25519PrivateKey.generate()
    signer = Ed25519EvidenceSigner(private_key=priv_key, key_id="key-secret-test")

    repr_str = repr(signer)
    str_val = str(signer)

    assert "key_id='key-secret-test'" in repr_str
    assert "private" not in repr_str.lower()
    assert "Ed25519PrivateKey" not in repr_str


def test_evidence_signing_failure_prevents_publication(tmp_path):
    """Test that if evidence signing fails or raises an error, orchestrator transitions to FAILED and does not publish PR."""
    source_repo = tmp_path / "failing_sign_repo"
    source_repo.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=source_repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test Bot"], cwd=source_repo, check=True)
    subprocess.run(["git", "config", "user.email", "bot@test.local"], cwd=source_repo, check=True)
    (source_repo / "app.py").write_text(
        "def query_user(user_input: str):\n"
        "    query = f\"SELECT * FROM users WHERE username = '{user_input}'\"\n"
        "    return query\n"
    )
    subprocess.run(["git", "add", "."], cwd=source_repo, check=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@test.local", "commit", "-qm", "initial"],
        cwd=source_repo,
        check=True,
    )
    head_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source_repo, text=True).strip()

    class BrokenSigner:
        def sign(self, evidence):
            raise RuntimeError("Hardware Security Module (HSM) signing failure")

    store = InMemoryJobStore()
    job = JobRecord(
        job_id="job-fail-signing-001",
        repository=str(source_repo),
        delivery_id="deliv-fail-sign",
        commit_sha=head_sha,
    )
    store.create(job)

    orchestrator = create_concrete_remediation_orchestrator(
        store=store,
        evidence_signer=BrokenSigner(),
    )

    result = orchestrator.run(job.job_id)

    assert result["state"] == JobState.FAILED.value
    assert result["verified"] is False
    assert "evidence signing failed" in result["error"]
    assert store.get_pr(job.job_id) is None


def test_successful_remediation_produces_signed_evidence(tmp_path):
    """Test full end-to-end remediation pipeline produces verified, cryptographically signed evidence."""
    source_repo = tmp_path / "signed_e2e_repo"
    source_repo.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=source_repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test Bot"], cwd=source_repo, check=True)
    subprocess.run(["git", "config", "user.email", "bot@test.local"], cwd=source_repo, check=True)
    (source_repo / "app.py").write_text(
        "def query_user(user_input: str):\n"
        "    query = f\"SELECT * FROM users WHERE username = '{user_input}'\"\n"
        "    return query\n"
    )
    subprocess.run(["git", "add", "."], cwd=source_repo, check=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@test.local", "commit", "-qm", "initial"],
        cwd=source_repo,
        check=True,
    )
    head_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source_repo, text=True).strip()

    priv_key = ed25519.Ed25519PrivateKey.generate()
    pub_key = priv_key.public_key()
    key_id = "test-e2e-signer-key"
    signer = Ed25519EvidenceSigner(private_key=priv_key, key_id=key_id)

    store = InMemoryJobStore()
    job = JobRecord(
        job_id="job-signed-e2e-001",
        repository=str(source_repo),
        delivery_id="deliv-signed-e2e",
        commit_sha=head_sha,
    )
    store.create(job)

    orchestrator = create_concrete_remediation_orchestrator(
        store=store,
        evidence_signer=signer,
    )

    result = orchestrator.run(job.job_id)

    assert result["state"] == JobState.PR_CREATED.value
    assert result["verified"] is True
    evidence = result["evidence"]

    assert evidence["sha256_digest"] is not None
    assert evidence["signature"] is not None
    assert evidence["signing_algorithm"] == "ed25519"
    assert evidence["signing_key_id"] == key_id

    # Verify signature
    key_store = PublicKeyStore()
    key_store.register_key(key_id, pub_key)
    res = verify_evidence(evidence, key_store=key_store)
    assert res.valid is True


def test_api_verify_evidence_endpoint(sample_evidence):
    """Test POST /evidence/verify endpoint in API."""
    signer = Ed25519EvidenceSigner()
    signed = signer.sign(sample_evidence)
    key_id = signer.key_id

    store = InMemoryJobStore()
    dispatcher = WebhookDispatcher(jobs=store, enqueue=lambda job_id: None)
    app = create_app(dispatcher=dispatcher, store=store, webhook_secret="test-sec", auth_enabled=False)
    client = TestClient(app)

    # Valid verification
    resp = client.post("/evidence/verify", json=signed)
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True
    assert data["key_id"] == key_id
    assert data["sha256_digest"] == signed["sha256_digest"]

    # Tampered verification
    tampered = dict(signed)
    tampered["verified"] = False
    resp2 = client.post("/evidence/verify", json=tampered)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["valid"] is False
    assert "tampered" in data2["error"].lower()
