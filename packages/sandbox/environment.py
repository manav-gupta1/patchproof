from __future__ import annotations

import os
from typing import Mapping

from packages.github.auth import sanitize_secret_text

# Explicitly allowed environment variables in sandbox
ALLOWED_ENV_VARS = frozenset({
    "PATH",
    "LANG",
    "LC_ALL",
    "PYTHONPATH",
    "PYTHONDONTWRITEBYTECODE",
    "TERM",
    "PYTHONUNBUFFERED",
    "VIRTUAL_ENV",
})

# Patterns matching sensitive keys or credentials
FORBIDDEN_ENV_PATTERNS = (
    "KEY",
    "TOKEN",
    "SECRET",
    "PASSWORD",
    "DATABASE",
    "POSTGRES",
    "REDIS",
    "AUTH",
    "CREDENTIAL",
    "PRIVATE",
    "JWT",
    "SIGNING",
    "API_KEY",
    "AWS_",
    "GITHUB_",
    "OPENAI_",
    "ANTHROPIC_",
    "PATCHPROOF_",
    "SSH_",
)

# Known explicit secrets
EXPLICIT_BLOCKED_KEYS = frozenset({
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GITHUB_TOKEN",
    "GITHUB_APP_PRIVATE_KEY",
    "GITHUB_APP_PRIVATE_KEY_PATH",
    "GITHUB_APP_ID",
    "GITHUB_WEBHOOK_SECRET",
    "DATABASE_URL",
    "POSTGRES_PASSWORD",
    "REDIS_URL",
    "REDIS_PASSWORD",
    "PATCHPROOF_API_KEY",
    "PATCHPROOF_API_KEYS",
    "PATCHPROOF_SIGNING_KEY",
    "PATCHPROOF_SIGNING_KEY_ID",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "SSH_AUTH_SOCK",
    "SSH_PRIVATE_KEY",
})


def is_sensitive_key(key: str) -> bool:
    """Return True if the key name suggests sensitive credentials."""
    upper = key.upper()
    if key in EXPLICIT_BLOCKED_KEYS:
        return True
    for pattern in FORBIDDEN_ENV_PATTERNS:
        if pattern in upper:
            return True
    return False


def build_isolated_environment(
    custom_env: Mapping[str, str] | None = None,
    base_env: Mapping[str, str] | None = None,
    allowlist: frozenset[str] | set[str] | None = None,
) -> dict[str, str]:
    """
    Construct a hardened, sanitized environment dictionary for sandbox execution.
    Never passes host environment wholesale. Strips all secret and credential keys.
    """
    effective_allowlist = allowlist if allowlist is not None else ALLOWED_ENV_VARS
    env: dict[str, str] = {
        "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "HOME": "/tmp",
        "TMPDIR": "/tmp",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUNBUFFERED": "1",
    }

    # Pull in approved variables from base_env (if present and non-sensitive)
    if base_env:
        for k, v in base_env.items():
            if k in effective_allowlist and k not in ("HOME", "TMPDIR", "TEMP") and not is_sensitive_key(k):
                env[k] = v

    # Add custom variables approved for this request
    if custom_env:
        for k, v in custom_env.items():
            if not is_sensitive_key(k):
                # Ensure no secrets embedded in values
                env[k] = sanitize_secret_text(str(v))

    return env
