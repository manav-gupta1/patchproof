from __future__ import annotations

from fastapi import Header, HTTPException, status
from packages.auth.models import TenantContext
from packages.auth.store import ApiKeyStore


def extract_bearer_token(
    authorization: str | None = None,
    x_api_key: str | None = None,
) -> str | None:
    """Extract token string from Authorization header or X-API-Key header."""
    if x_api_key and x_api_key.strip():
        return x_api_key.strip()
    if not authorization or not authorization.strip():
        return None
    parts = authorization.strip().split()
    if len(parts) == 2 and parts[0].lower() in {"bearer", "apikey", "token"}:
        return parts[1]
    if len(parts) == 1 and not parts[0].lower().startswith("bearer"):
        return parts[0]
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid Authorization header format. Expected 'Bearer <token>'",
        headers={"WWW-Authenticate": 'Bearer realm="PatchProof"'},
    )
