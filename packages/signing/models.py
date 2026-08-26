from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class SigningAlgorithm(str, Enum):
    ED25519 = "ed25519"


class SignatureBundle(BaseModel):
    sha256_digest: str = Field(description="Hex-encoded SHA-256 digest of canonical evidence payload")
    signature: str = Field(description="Hex-encoded Ed25519 cryptographic signature")
    signing_algorithm: str = Field(default="ed25519", description="Asymmetric signature algorithm")
    signing_key_id: str = Field(description="Key ID of the public key required to verify this signature")
    signed_at: str = Field(description="ISO8601 timestamp when signature was computed")


class VerificationResult(BaseModel):
    valid: bool = Field(description="Whether the cryptographic signature and digest are valid")
    key_id: str | None = Field(default=None, description="Key ID used during verification")
    signing_algorithm: str | None = Field(default=None, description="Signature algorithm verified")
    sha256_digest: str | None = Field(default=None, description="Computed SHA-256 digest of evidence")
    error: str | None = Field(default=None, description="Diagnostic reason if verification failed")
