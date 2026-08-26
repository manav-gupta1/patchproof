from __future__ import annotations
from dataclasses import dataclass


class SandboxPolicyError(ValueError):
    pass


@dataclass(frozen=True)
class SandboxPolicy:
    timeout_seconds: int = 900
    memory_mb: int = 1024
    cpu_seconds: int = 300
    pids_limit: int = 256
    network_enabled: bool = False
    network: bool | None = None
    readonly_root: bool = True

    @property
    def pids(self):
        """Compatibility alias for the sandbox executor contract."""
        return self.pids_limit

    @property
    def max_output_bytes(self):
        """Bound captured output to prevent evidence/memory amplification."""
        return 1_048_576

    def __post_init__(self):
        if self.network is not None and self.network != self.network_enabled:
            object.__setattr__(self, "network_enabled", self.network)

    def validate(self):
        if not 1 <= self.timeout_seconds <= 3600:
            raise SandboxPolicyError("timeout must be between 1 and 3600 seconds")
        if not 128 <= self.memory_mb <= 16384:
            raise SandboxPolicyError("memory limit is outside the supported range")
        if not 1 <= self.cpu_seconds <= 3600:
            raise SandboxPolicyError("invalid CPU limit")
        if not 16 <= self.pids_limit <= 4096:
            raise SandboxPolicyError("invalid PID limit")
        if self.network_enabled:
            raise SandboxPolicyError("network access is disabled by policy")
        if not self.readonly_root:
            raise SandboxPolicyError("sandbox root must be read-only")
