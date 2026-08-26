from __future__ import annotations

import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from packages.github.transport import GitHubAPIError, GitHubAuthError


def sanitize_secret_text(text: str) -> str:
    """Scrub tokens, private keys, and credential patterns from diagnostic strings."""
    if not text:
        return ""
    # Scrub PEM blocks
    text = re.sub(
        r"-----BEGIN[ A-Z_-]+KEY-----[\s\S]*?-----END[ A-Z_-]+KEY-----",
        "[REDACTED_PRIVATE_KEY]",
        text,
    )
    # Scrub GitHub personal/installation tokens (ghp_, ghs_, gho_, etc.)
    text = re.sub(r"gh[psorub]_[A-Za-z0-9_]{16,}", "[REDACTED_TOKEN]", text)
    # Scrub URLs containing tokens (https://x-access-token:xyz@github.com/...)
    text = re.sub(
        r"https?://[^:\s]+:[^@\s]+@github\.com",
        "https://[REDACTED_AUTH]@github.com",
        text,
    )
    # Scrub Bearer tokens
    text = re.sub(r"Bearer\s+[A-Za-z0-9_\-\.]{20,}", "Bearer [REDACTED_JWT]", text)
    return text


@dataclass(frozen=True)
class InstallationToken:
    """GitHub App short-lived installation access token."""

    token: str
    expires_at: int

    def __repr__(self) -> str:
        masked = f"{self.token[:4]}...{self.token[-4:]}" if len(self.token) >= 8 else "[REDACTED]"
        return f"InstallationToken(token='{masked}', expires_at={self.expires_at})"

    def __str__(self) -> str:
        return self.__repr__()

    @property
    def expired(self) -> bool:
        return int(time.time()) >= self.expires_at - 60


@dataclass(frozen=True)
class GitHubAppCredentials:
    """Structured GitHub App credentials with secret masking."""

    app_id: str
    private_key_pem: str
    installation_id: int | None = None
    api_url: str = "https://api.github.com"

    def __repr__(self) -> str:
        return (
            f"GitHubAppCredentials(app_id={self.app_id!r}, "
            f"private_key_pem='[REDACTED]', "
            f"installation_id={self.installation_id!r}, "
            f"api_url={self.api_url!r})"
        )

    def __str__(self) -> str:
        return self.__repr__()

    @classmethod
    def from_env(cls) -> GitHubAppCredentials:
        """Load GitHub App credentials from environment variables."""
        app_id = (
            os.environ.get("GITHUB_APP_ID")
            or os.environ.get("PATCHPROOF_GITHUB_APP_ID")
            or ""
        ).strip()

        private_key = (
            os.environ.get("GITHUB_APP_PRIVATE_KEY")
            or os.environ.get("PATCHPROOF_GITHUB_APP_PRIVATE_KEY")
            or ""
        ).strip()

        # If private key path was supplied instead of raw PEM string
        key_path = (
            os.environ.get("GITHUB_APP_PRIVATE_KEY_PATH")
            or os.environ.get("PATCHPROOF_GITHUB_APP_PRIVATE_KEY_PATH")
            or ""
        ).strip()
        if not private_key and key_path:
            path = Path(key_path)
            if not path.exists():
                raise GitHubAuthError(f"GitHub App private key file not found: {key_path}")
            private_key = path.read_text().strip()

        inst_id_raw = (
            os.environ.get("GITHUB_APP_INSTALLATION_ID")
            or os.environ.get("PATCHPROOF_GITHUB_INSTALLATION_ID")
            or ""
        ).strip()
        installation_id = int(inst_id_raw) if inst_id_raw.isdigit() else None

        api_url = (
            os.environ.get("GITHUB_API_URL")
            or os.environ.get("PATCHPROOF_GITHUB_API_URL")
            or "https://api.github.com"
        ).strip()

        if not app_id:
            raise GitHubAuthError("Missing required GITHUB_APP_ID")
        if not private_key:
            raise GitHubAuthError("Missing required GITHUB_APP_PRIVATE_KEY or GITHUB_APP_PRIVATE_KEY_PATH")

        return cls(
            app_id=app_id,
            private_key_pem=private_key,
            installation_id=installation_id,
            api_url=api_url,
        )


def create_app_jwt(app_id: str, private_key_pem: str) -> str:
    """Generate an RS256-signed JWT for GitHub App authentication."""
    try:
        import jwt
    except ImportError as exc:
        raise GitHubAuthError("PyJWT package is required for GitHub App JWT generation") from exc

    if not app_id:
        raise GitHubAuthError("app_id is required for JWT generation")
    if not private_key_pem or "-----BEGIN" not in private_key_pem:
        raise GitHubAuthError("Invalid or missing RSA private key PEM format")

    now = int(time.time())
    payload = {
        "iat": now - 60,
        "exp": now + (10 * 60),
        "iss": str(app_id),
    }

    try:
        token = jwt.encode(payload, private_key_pem, algorithm="RS256")
        return token if isinstance(token, str) else token.decode("utf-8")
    except Exception as exc:
        raise GitHubAuthError(f"Failed to sign GitHub App JWT: {sanitize_secret_text(str(exc))}") from exc


def request_installation_token(
    jwt_token: str,
    installation_id: int,
    api_url: str = "https://api.github.com",
) -> dict[str, Any]:
    """Exchange a GitHub App JWT for a short-lived installation access token."""
    url = f"{api_url.rstrip('/')}/app/installations/{installation_id}/access_tokens"
    req = urllib.request.Request(
        url,
        data=b"{}",
        method="POST",
        headers={
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "PatchProof-Security-Remediator",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            exp = data.get("expires_at")
            if isinstance(exp, str):
                dt = datetime.fromisoformat(exp.replace("Z", "+00:00"))
                exp_ts = int(dt.timestamp())
            elif isinstance(exp, (int, float)):
                exp_ts = int(exp)
            else:
                exp_ts = int(time.time()) + 3600
            return {
                "token": data.get("token"),
                "expires_at": exp_ts,
            }
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        if exc.code == 401:
            raise GitHubAuthError("GitHub App authentication failed (401 Unauthorized): invalid credentials") from exc
        if exc.code == 404:
            raise GitHubAuthError(f"GitHub installation {installation_id} not found (404 Not Found)") from exc
        raise GitHubAuthError(f"GitHub installation token request failed with status {exc.code}: {detail[:200]}") from exc
    except urllib.error.URLError as exc:
        raise GitHubAuthError(f"GitHub API connection failure: {exc.reason}") from exc


class GitHubAppAuth:
    """Production GitHub App authentication manager supporting caching, thread-safety, and mock client injection."""

    def __init__(
        self,
        app_id: str,
        private_key_pem: str,
        github_client: object = None,
        api_url: str = "https://api.github.com",
    ) -> None:
        if not app_id:
            raise GitHubAuthError("app_id is required")
        if not private_key_pem:
            raise GitHubAuthError("private_key_pem is required")
        self.app_id = str(app_id)
        self.private_key_pem = private_key_pem
        self.github = github_client
        self.api_url = api_url
        self._cached_tokens: dict[int, InstallationToken] = {}
        self._lock = threading.Lock()

    def __repr__(self) -> str:
        return f"GitHubAppAuth(app_id={self.app_id!r}, private_key_pem='[REDACTED]')"

    def create_jwt(self) -> str:
        """Create a signed JWT, delegating to injected client if available."""
        if self.github is not None and hasattr(self.github, "create_app_jwt"):
            return self.github.create_app_jwt(
                app_id=self.app_id,
                private_key_pem=self.private_key_pem,
            )
        return create_app_jwt(self.app_id, self.private_key_pem)

    def installation_token(self, installation_id: int) -> InstallationToken:
        """Retrieve a valid installation access token, using cache when active."""
        if not installation_id:
            raise GitHubAuthError("installation_id is required")

        with self._lock:
            cached = self._cached_tokens.get(installation_id)
            if cached and not cached.expired:
                return cached

            if self.github is not None and hasattr(self.github, "create_installation_token"):
                jwt_token = self.create_jwt()
                result = self.github.create_installation_token(
                    jwt=jwt_token,
                    installation_id=installation_id,
                )
                token = result.get("token")
                expires_at = result.get("expires_at")
                if not token or not expires_at:
                    raise GitHubAuthError("GitHub did not return an installation token")
                inst_token = InstallationToken(token=token, expires_at=int(expires_at))
                self._cached_tokens[installation_id] = inst_token
                return inst_token

            jwt_token = self.create_jwt()
            result = request_installation_token(jwt_token, installation_id, self.api_url)
            token = result.get("token")
            expires_at = result.get("expires_at")
            if not token or not expires_at:
                raise GitHubAuthError("GitHub did not return an installation token")
            inst_token = InstallationToken(token=token, expires_at=int(expires_at))
            self._cached_tokens[installation_id] = inst_token
            return inst_token
