from __future__ import annotations

import os
from typing import Any

from packages.sandbox.models import SandboxUnavailableError
from packages.sandbox.provider import SandboxProvider
from packages.sandbox.providers.container import DockerContainerSandboxProvider
from packages.sandbox.providers.gvisor import GVisorSandboxProvider
from packages.sandbox.providers.local import LocalProcessSandboxProvider


def get_sandbox_provider(
    provider_type: str | None = None,
    image: str | None = None,
    **kwargs: Any,
) -> SandboxProvider:
    """
    Factory to obtain the configured SandboxProvider.
    Enforces fail-closed semantics: never silently falls back to local execution
    when production or container/gVisor runtime is requested.
    """
    requested = (provider_type or os.getenv("PATCHPROOF_SANDBOX_PROVIDER", "")).strip().lower()
    img = image or os.getenv("PATCHPROOF_SANDBOX_IMAGE", "patchproof/runner:latest")
    is_production = os.getenv("PATCHPROOF_ENV", "").lower() == "production"
    allow_local = os.getenv("PATCHPROOF_ALLOW_LOCAL_SANDBOX", "0") == "1"

    if requested in ("gvisor", "runsc"):
        return GVisorSandboxProvider(image=img, **kwargs)

    if requested in ("container", "docker"):
        return DockerContainerSandboxProvider(image=img, **kwargs)

    if requested in ("local", "process"):
        if is_production and not allow_local:
            raise SandboxUnavailableError(
                "Local process sandbox is prohibited in production environment without PATCHPROOF_ALLOW_LOCAL_SANDBOX=1"
            )
        return LocalProcessSandboxProvider(**kwargs)

    # Default resolution when not explicitly set
    if is_production:
        if allow_local:
            return LocalProcessSandboxProvider(**kwargs)
        # In production, default to container provider
        return DockerContainerSandboxProvider(image=img, **kwargs)

    # In development/test mode without explicit provider, default to local provider
    return LocalProcessSandboxProvider(**kwargs)
