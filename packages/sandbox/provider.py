from __future__ import annotations

from typing import Any, Protocol, Sequence, runtime_checkable

from packages.sandbox.models import SandboxRequest, SandboxResult


@runtime_checkable
class SandboxProvider(Protocol):
    """Protocol for sandbox providers executing commands in isolated environments."""

    @property
    def provider_name(self) -> str:
        """Name of the sandbox provider (e.g. 'local', 'container', 'gvisor')."""
        ...

    @property
    def runtime_name(self) -> str:
        """Name of the runtime backend (e.g. 'process', 'runc', 'runsc')."""
        ...

    def run(self, request: SandboxRequest | Any, **kwargs: Any) -> SandboxResult:
        """
        Execute a command within the isolated sandbox.
        Accepts either a SandboxRequest object or (workspace, command, **kwargs) for backward compatibility.
        """
        ...
