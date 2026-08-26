from __future__ import annotations

import base64
import binascii
import os
from typing import Protocol
from cryptography.hazmat.primitives.asymmetric import ed25519


class PublicKeyStore:
    """Registry mapping key IDs to Ed25519 public keys for verification and key rotation."""

    def __init__(self) -> None:
        self._keys: dict[str, ed25519.Ed25519PublicKey] = {}

    def register_key(self, key_id: str, public_key: ed25519.Ed25519PublicKey) -> None:
        if not key_id or not key_id.strip():
            raise ValueError("key_id cannot be empty")
        self._keys[key_id.strip()] = public_key

    def register_raw_public_key(self, key_id: str, raw_bytes: bytes) -> None:
        if len(raw_bytes) != 32:
            raise ValueError(f"Ed25519 public key must be 32 bytes, got {len(raw_bytes)}")
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(raw_bytes)
        self.register_key(key_id, public_key)

    def get_key(self, key_id: str) -> ed25519.Ed25519PublicKey | None:
        return self._keys.get(key_id.strip())

    @classmethod
    def from_env(cls) -> PublicKeyStore:
        store = cls()
        key_id = os.environ.get("PATCHPROOF_SIGNING_KEY_ID", "patchproof-key-1")
        pub_hex = os.environ.get("PATCHPROOF_SIGNING_PUBLIC_KEY")
        if pub_hex:
            try:
                raw = binascii.unhexlify(pub_hex.strip())
                store.register_raw_public_key(key_id, raw)
            except Exception:
                pass
        return store


# Deterministic default keypair used for testing/local development when no environment key is supplied
_DEV_SEED_32_BYTES = b"patchproof-dev-signing-seed-0001"
_DEV_PRIVATE_KEY = ed25519.Ed25519PrivateKey.from_private_bytes(_DEV_SEED_32_BYTES)
_DEV_PUBLIC_KEY = _DEV_PRIVATE_KEY.public_key()
_DEV_KEY_ID = "patchproof-dev-key-1"


def get_configured_private_key() -> tuple[str, ed25519.Ed25519PrivateKey]:
    """Resolve the active signing key ID and private key from configuration or fallback."""
    key_id = os.environ.get("PATCHPROOF_SIGNING_KEY_ID", _DEV_KEY_ID)
    priv_hex = os.environ.get("PATCHPROOF_SIGNING_PRIVATE_KEY")
    if priv_hex:
        try:
            raw = binascii.unhexlify(priv_hex.strip())
            if len(raw) == 32:
                return key_id, ed25519.Ed25519PrivateKey.from_private_bytes(raw)
        except Exception:
            pass

    return key_id, _DEV_PRIVATE_KEY


def get_default_key_store() -> PublicKeyStore:
    """Build public key store with default dev key and environment public keys."""
    store = PublicKeyStore.from_env()
    store.register_key(_DEV_KEY_ID, _DEV_PUBLIC_KEY)
    return store
