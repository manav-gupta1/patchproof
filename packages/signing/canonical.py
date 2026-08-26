from __future__ import annotations

import hashlib
import json
from typing import Any

# Fields excluded from the canonical payload when computing the pre-signature digest
SIGNATURE_FIELDS = {
    "sha256_digest",
    "signature",
    "signing_algorithm",
    "signing_key_id",
    "signed_at",
    "pr",
}


def _strip_signature_fields(data: Any) -> Any:
    """Recursively copy data removing signature metadata fields."""
    if isinstance(data, dict):
        return {
            k: _strip_signature_fields(v)
            for k, v in data.items()
            if k not in SIGNATURE_FIELDS
        }
    if isinstance(data, list):
        return [_strip_signature_fields(item) for item in data]
    return data


def canonicalize_evidence(data: dict[str, Any]) -> bytes:
    """Deterministically encode evidence data to canonical UTF-8 JSON bytes.
    
    Invariants:
    1. Signature metadata fields are excluded.
    2. Dictionary keys are sorted alphabetically.
    3. Formatting uses compact separators (',', ':') with no extra whitespace.
    4. Strings are encoded in UTF-8 without ASCII escaping.
    """
    clean_data = _strip_signature_fields(data)
    canonical_str = json.dumps(
        clean_data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return canonical_str.encode("utf-8")


def compute_evidence_digest(data: dict[str, Any]) -> str:
    """Compute the hexadecimal SHA-256 digest over the canonicalized evidence."""
    canonical_bytes = canonicalize_evidence(data)
    return hashlib.sha256(canonical_bytes).hexdigest()
