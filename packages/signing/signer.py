from __future__ import annotations

import binascii
import hmac
from datetime import datetime, timezone
from typing import Any, Protocol

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ed25519

from packages.signing.canonical import canonicalize_evidence, compute_evidence_digest
from packages.signing.keys import (
    PublicKeyStore,
    get_configured_private_key,
    get_default_key_store,
)
from packages.signing.models import SignatureBundle, VerificationResult


class EvidenceSignerProtocol(Protocol):
    """Protocol for cryptographic evidence signers."""

    def sign(self, evidence: dict[str, Any]) -> dict[str, Any]: ...


class EvidenceVerifierProtocol(Protocol):
    """Protocol for cryptographic evidence verifiers."""

    def verify(self, evidence: dict[str, Any]) -> VerificationResult: ...


class Ed25519EvidenceSigner:
    """Tamper-evident Ed25519 evidence signer."""

    def __init__(
        self,
        private_key: ed25519.Ed25519PrivateKey | None = None,
        key_id: str | None = None,
    ) -> None:
        if private_key is None or key_id is None:
            resolved_id, resolved_key = get_configured_private_key()
            self._key_id = key_id or resolved_id
            self._private_key = private_key or resolved_key
        else:
            self._key_id = key_id
            self._private_key = private_key

    @property
    def key_id(self) -> str:
        return self._key_id

    @property
    def public_key(self) -> ed25519.Ed25519PublicKey:
        return self._private_key.public_key()

    def __repr__(self) -> str:
        return f"<Ed25519EvidenceSigner key_id='{self._key_id}'>"

    def __str__(self) -> str:
        return f"Ed25519EvidenceSigner(key_id='{self._key_id}')"

    def sign(self, evidence: dict[str, Any]) -> dict[str, Any]:
        """Sign canonical evidence payload and return bundle with cryptographic signature."""
        if not isinstance(evidence, dict):
            raise TypeError("Evidence payload must be a dictionary")

        canonical_bytes = canonicalize_evidence(evidence)
        sha256_hex = compute_evidence_digest(evidence)

        # Sign the canonical UTF-8 bytes directly using Ed25519
        signature_bytes = self._private_key.sign(canonical_bytes)
        signature_hex = binascii.hexlify(signature_bytes).decode("ascii")

        signed_evidence = dict(evidence)
        signed_evidence["sha256_digest"] = sha256_hex
        signed_evidence["signature"] = signature_hex
        signed_evidence["signing_algorithm"] = "ed25519"
        signed_evidence["signing_key_id"] = self._key_id
        signed_evidence["signed_at"] = datetime.now(timezone.utc).isoformat()

        return signed_evidence


class Ed25519EvidenceVerifier:
    """Verifies Ed25519 cryptographic signatures and canonical digests on evidence payloads."""

    def __init__(self, key_store: PublicKeyStore | None = None) -> None:
        self.key_store = key_store or get_default_key_store()

    def verify(self, evidence: dict[str, Any]) -> VerificationResult:
        if not isinstance(evidence, dict):
            return VerificationResult(
                valid=False,
                error="Evidence payload must be a dictionary",
            )

        key_id = evidence.get("signing_key_id")
        if not key_id:
            return VerificationResult(
                valid=False,
                error="Missing required 'signing_key_id' in evidence",
            )

        signature_hex = evidence.get("signature")
        if not signature_hex:
            return VerificationResult(
                valid=False,
                key_id=key_id,
                error="Missing required 'signature' in evidence",
            )

        expected_digest = evidence.get("sha256_digest")
        if not expected_digest:
            return VerificationResult(
                valid=False,
                key_id=key_id,
                error="Missing required 'sha256_digest' in evidence",
            )

        algorithm = evidence.get("signing_algorithm", "ed25519")
        if algorithm != "ed25519":
            return VerificationResult(
                valid=False,
                key_id=key_id,
                signing_algorithm=algorithm,
                error=f"Unsupported signing algorithm: {algorithm}",
            )

        # 1. Verify canonical SHA-256 digest matches payload
        computed_digest = compute_evidence_digest(evidence)
        if not hmac.compare_digest(computed_digest.lower(), expected_digest.lower()):
            return VerificationResult(
                valid=False,
                key_id=key_id,
                signing_algorithm=algorithm,
                sha256_digest=computed_digest,
                error="Computed SHA-256 digest does not match provided sha256_digest (payload was tampered with)",
            )

        # 2. Resolve public key from key store
        public_key = self.key_store.get_key(key_id)
        if public_key is None:
            return VerificationResult(
                valid=False,
                key_id=key_id,
                signing_algorithm=algorithm,
                sha256_digest=computed_digest,
                error=f"Public key for key_id '{key_id}' is not registered in key store",
            )

        # 3. Decode and verify Ed25519 signature
        try:
            sig_bytes = binascii.unhexlify(signature_hex.strip())
        except Exception as e:
            return VerificationResult(
                valid=False,
                key_id=key_id,
                signing_algorithm=algorithm,
                sha256_digest=computed_digest,
                error=f"Invalid signature encoding: {e}",
            )

        canonical_bytes = canonicalize_evidence(evidence)
        try:
            public_key.verify(sig_bytes, canonical_bytes)
        except InvalidSignature:
            return VerificationResult(
                valid=False,
                key_id=key_id,
                signing_algorithm=algorithm,
                sha256_digest=computed_digest,
                error="Cryptographic signature verification failed (signature mismatch)",
            )
        except Exception as e:
            return VerificationResult(
                valid=False,
                key_id=key_id,
                signing_algorithm=algorithm,
                sha256_digest=computed_digest,
                error=f"Signature verification error: {e}",
            )

        return VerificationResult(
            valid=True,
            key_id=key_id,
            signing_algorithm=algorithm,
            sha256_digest=computed_digest,
            error=None,
        )


def verify_evidence(
    evidence: dict[str, Any],
    key_store: PublicKeyStore | None = None,
) -> VerificationResult:
    """Convenience function to verify signed evidence against a public key store."""
    verifier = Ed25519EvidenceVerifier(key_store=key_store)
    return verifier.verify(evidence)
