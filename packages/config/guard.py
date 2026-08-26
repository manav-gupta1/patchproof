from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


INSECURE_SECRETS = {
    "dev-secret",
    "development-secret",
    "secret",
    "123456",
    "default",
    "test",
    "test-secret",
    "changeme",
    "password",
}


class ProductionConfigurationError(ValueError):
    """Raised when production environment is configured with insecure or development settings."""


@dataclass
class ProductionConfigValidation:
    is_production: bool
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def enforce(self) -> None:
        """Fail closed if validation fails in production mode."""
        if self.is_production and not self.valid:
            error_details = "\n - ".join(self.errors)
            raise ProductionConfigurationError(
                f"Production configuration guard failed with {len(self.errors)} error(s):\n - {error_details}"
            )


def validate_production_configuration(env: dict[str, str] | None = None) -> ProductionConfigValidation:
    """Audit runtime environment variables to ensure production cannot start with insecure defaults."""
    environ = os.environ if env is None else env

    environment = (
        environ.get("PATCHPROOF_ENVIRONMENT", "")
        or environ.get("ENV", "")
        or environ.get("ENVIRONMENT", "")
    ).strip().lower()

    is_prod = environment in ("production", "prod")

    errors: list[str] = []
    warnings: list[str] = []

    if is_prod:
        # 1. Authentication Check
        auth_enabled = environ.get("PATCHPROOF_AUTH_ENABLED", "true").strip().lower()
        if auth_enabled in ("0", "false", "no", "disabled"):
            errors.append("Authentication cannot be disabled in production (PATCHPROOF_AUTH_ENABLED=false)")

        # 2. Webhook Secret Check
        webhook_secret = environ.get("GITHUB_WEBHOOK_SECRET", "").strip()
        if not webhook_secret:
            errors.append("GITHUB_WEBHOOK_SECRET is required in production")
        elif webhook_secret in INSECURE_SECRETS or len(webhook_secret) < 16:
            errors.append("GITHUB_WEBHOOK_SECRET uses an insecure or default development secret (must be >= 16 chars)")

        # 3. Integration Test Mode Guard
        integration_mode = environ.get("PATCHPROOF_GITHUB_INTEGRATION_TEST", "").strip().lower()
        if integration_mode in ("1", "true", "yes"):
            errors.append("PATCHPROOF_GITHUB_INTEGRATION_TEST must not be enabled in production")

        # 4. GitHub App Credentials
        github_enabled = environ.get("PATCHPROOF_GITHUB_ENABLED", "true").strip().lower()
        if github_enabled in ("1", "true", "yes"):
            app_id = environ.get("GITHUB_APP_ID", "").strip()
            private_key = environ.get("GITHUB_APP_PRIVATE_KEY", "").strip()
            private_key_path = environ.get("GITHUB_APP_PRIVATE_KEY_PATH", "").strip()

            if not app_id:
                errors.append("GITHUB_APP_ID is required for GitHub App publication in production")
            if not private_key and not private_key_path:
                errors.append("GITHUB_APP_PRIVATE_KEY or GITHUB_APP_PRIVATE_KEY_PATH is required in production")

        # 5. Sandbox Provider Check
        sandbox_provider = environ.get("PATCHPROOF_SANDBOX_PROVIDER", "").strip().lower()
        if sandbox_provider in ("none", "disabled", "local_unsafe"):
            errors.append(f"Insecure sandbox provider '{sandbox_provider}' is not permitted in production")
        elif sandbox_provider and sandbox_provider not in ("gvisor", "docker", "bubblewrap", "container"):
            warnings.append(f"Unrecognized sandbox provider '{sandbox_provider}'. Ensure hardened runtime isolation.")

        # 6. CORS Configuration Guard
        cors_origins = environ.get("PATCHPROOF_CORS_ORIGINS", "").strip()
        if is_prod and cors_origins in ("*", ""):
            errors.append("Wildcard CORS origin (PATCHPROOF_CORS_ORIGINS=*) is not permitted in production. Explicit allowed origins required.")

    return ProductionConfigValidation(
        is_production=is_prod,
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )
