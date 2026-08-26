from __future__ import annotations

import hashlib
import hmac
import json
import os
from typing import Any
from packages.auth.models import TenantContext


def hash_api_token(token: str) -> str:
    """Compute deterministic SHA-256 digest of token for safe indexing and lookup."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class ApiKeyStore:
    """Secure API key token store mapping SHA-256 token digests to TenantContext."""

    def __init__(self):
        # Maps token_sha256 -> TenantContext
        self._tokens: dict[str, TenantContext] = {}

    def register_token(
        self,
        token: str,
        tenant: TenantContext,
    ) -> None:
        if not token or not token.strip():
            raise ValueError("API token cannot be empty")
        token_hash = hash_api_token(token.strip())
        self._tokens[token_hash] = tenant

    def authenticate_token(self, provided_token: str) -> TenantContext | None:
        if not provided_token or not provided_token.strip():
            return None
        provided_hash = hash_api_token(provided_token.strip())
        # Constant-time comparison across registered digests to prevent timing attacks
        matched_tenant = None
        for registered_hash, tenant in self._tokens.items():
            if hmac.compare_digest(provided_hash, registered_hash):
                matched_tenant = tenant
        return matched_tenant

    @classmethod
    def from_env(cls) -> ApiKeyStore:
        store = cls()

        # 1. Single API key configuration (PATCHPROOF_API_KEY)
        single_key = os.environ.get("PATCHPROOF_API_KEY")
        if single_key and single_key.strip():
            default_tenant = TenantContext(
                tenant_id="default-tenant",
                name="Default Production Tenant",
                allowed_repositories=("*",),
                is_admin=True,
            )
            store.register_token(single_key.strip(), default_tenant)

        # 2. Multi-tenant JSON mappings (PATCHPROOF_API_KEYS)
        # Format: {"token_val": {"tenant_id": "t1", "name": "Acme", "allowed_repositories": ["acme/*"]}}
        raw_keys = os.environ.get("PATCHPROOF_API_KEYS")
        if raw_keys and raw_keys.strip():
            try:
                data = json.loads(raw_keys)
                if isinstance(data, dict):
                    for token_val, config in data.items():
                        if isinstance(config, dict):
                            tenant = TenantContext(
                                tenant_id=config.get("tenant_id", "tenant-custom"),
                                name=config.get("name", "Custom Tenant"),
                                allowed_repositories=tuple(config.get("allowed_repositories", ["*"])),
                                is_admin=bool(config.get("is_admin", False)),
                            )
                            store.register_token(token_val, tenant)
            except Exception:
                pass

        return store
