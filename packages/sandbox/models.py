from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Sequence
from pydantic import BaseModel, Field


class NetworkPolicy(str, Enum):
    DENY = "deny"
    NONE = "none"
    RESTRICTED = "restricted"
    ALLOW = "allow"


class SandboxError(Exception):
    """Base exception for sandbox runtime errors."""
    pass


class SandboxUnavailableError(SandboxError):
    """Raised when the requested sandbox provider or runtime is unavailable."""
    pass


class SandboxTimeoutError(SandboxError):
    """Raised when a sandbox execution times out."""
    pass


class SandboxResourceLimitError(SandboxError):
    """Raised when a sandbox execution exceeds resource limits."""
    pass


class SandboxSecurityError(SandboxError):
    """Raised when a security boundary violation is detected."""
    pass


@dataclass(frozen=True)
class SandboxRequest:
    command: Sequence[str] | str
    workspace_path: Path | str
    environment: dict[str, str] | None = None
    working_directory: str = "/workspace"
    timeout_seconds: float = 60.0
    memory_limit_mb: int = 512
    cpu_limit: float = 1.0
    pids_limit: int = 100
    read_only_root: bool = True
    non_root_uid: int = 10001
    network_policy: NetworkPolicy | str = NetworkPolicy.DENY
    network_allowlist: list[str] | None = None
    max_output_bytes: int = 100 * 1024  # 100 KB default

    @property
    def cmd_list(self) -> list[str]:
        if isinstance(self.command, str):
            return [self.command]
        return list(self.command)


@dataclass(frozen=True, init=False)
class SandboxResult:
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool
    resource_limited: bool
    output_truncated: bool
    original_output_size: int
    captured_output_size: int
    provider: str
    runtime: str
    sandbox_id: str | None
    network_policy: str
    command: list[str]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Handle keyword arguments
        if kwargs:
            exit_code = kwargs.get("exit_code", kwargs.get("returncode", 0))
            stdout = kwargs.get("stdout", "")
            stderr = kwargs.get("stderr", "")
            if "duration_seconds" in kwargs:
                duration_sec = float(kwargs["duration_seconds"])
            elif "duration_ms" in kwargs:
                duration_sec = float(kwargs["duration_ms"]) / 1000.0
            else:
                duration_sec = 0.0

            timed_out = bool(kwargs.get("timed_out", False))
            resource_limited = bool(kwargs.get("resource_limited", False))
            output_truncated = bool(kwargs.get("output_truncated", False))
            orig_size = int(kwargs.get("original_output_size", len(stdout) + len(stderr)))
            captured_size = int(kwargs.get("captured_output_size", len(stdout) + len(stderr)))
            provider = str(kwargs.get("provider", "unknown"))
            runtime = str(kwargs.get("runtime", "unknown"))
            sandbox_id = kwargs.get("sandbox_id")
            network_policy = str(kwargs.get("network_policy", "deny"))
            command = list(kwargs.get("command", kwargs.get("argv", [])))

            object.__setattr__(self, "exit_code", int(exit_code) if exit_code is not None else 0)
            object.__setattr__(self, "stdout", str(stdout))
            object.__setattr__(self, "stderr", str(stderr))
            object.__setattr__(self, "duration_seconds", float(duration_sec))
            object.__setattr__(self, "timed_out", timed_out)
            object.__setattr__(self, "resource_limited", resource_limited)
            object.__setattr__(self, "output_truncated", output_truncated)
            object.__setattr__(self, "original_output_size", orig_size)
            object.__setattr__(self, "captured_output_size", captured_size)
            object.__setattr__(self, "provider", provider)
            object.__setattr__(self, "runtime", runtime)
            object.__setattr__(self, "sandbox_id", sandbox_id)
            object.__setattr__(self, "network_policy", network_policy)
            object.__setattr__(self, "command", command)
            return

        # Handle positional arguments
        if len(args) == 4:
            if isinstance(args[0], bool):
                passed, exit_code, stdout, stderr = args
                duration_sec = 0.0
            elif isinstance(args[0], int) and isinstance(args[1], str):
                exit_code, stdout, stderr, duration_sec = args
            else:
                passed, exit_code, stdout, stderr = args
                duration_sec = 0.0
        elif len(args) == 5:
            passed, exit_code, stdout, stderr, duration_sec = args
        else:
            exit_code = 0
            stdout = ""
            stderr = ""
            duration_sec = 0.0

        object.__setattr__(self, "exit_code", int(exit_code) if exit_code is not None else 0)
        object.__setattr__(self, "stdout", str(stdout))
        object.__setattr__(self, "stderr", str(stderr))
        object.__setattr__(self, "duration_seconds", float(duration_sec))
        object.__setattr__(self, "timed_out", False)
        object.__setattr__(self, "resource_limited", False)
        object.__setattr__(self, "output_truncated", False)
        object.__setattr__(self, "original_output_size", len(stdout) + len(stderr))
        object.__setattr__(self, "captured_output_size", len(stdout) + len(stderr))
        object.__setattr__(self, "provider", "unknown")
        object.__setattr__(self, "runtime", "unknown")
        object.__setattr__(self, "sandbox_id", None)
        object.__setattr__(self, "network_policy", "deny")
        object.__setattr__(self, "command", [])

    @property
    def passed(self) -> bool:
        return self.exit_code == 0 and not self.timed_out and not self.resource_limited

    @property
    def succeeded(self) -> bool:
        return self.passed

    @property
    def returncode(self) -> int:
        return self.exit_code

    @property
    def combined_output(self) -> str:
        if self.stderr:
            return f"{self.stdout}\n{self.stderr}" if self.stdout else self.stderr
        return self.stdout

    @property
    def duration_ms(self) -> int:
        return int(self.duration_seconds * 1000)

    @property
    def argv(self) -> list[str]:
        return self.command

    @property
    def policy(self) -> dict[str, Any]:
        return {"network": self.network_policy not in ("allow",), "readonly_root": True}

    @property
    def sandboxed(self) -> bool:
        return self.provider not in ("unprotected",)

    @property
    def stdout_sha256(self) -> str:
        return hashlib.sha256(self.stdout.encode("utf-8", errors="replace")).hexdigest()

    @property
    def stderr_sha256(self) -> str:
        return hashlib.sha256(self.stderr.encode("utf-8", errors="replace")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "exit_code": self.exit_code,
            "passed": self.passed,
            "duration_seconds": self.duration_seconds,
            "timed_out": self.timed_out,
            "resource_limited": self.resource_limited,
            "output_truncated": self.output_truncated,
            "original_output_size": self.original_output_size,
            "captured_output_size": self.captured_output_size,
            "provider": self.provider,
            "runtime": self.runtime,
            "sandbox_id": self.sandbox_id,
            "network_policy": self.network_policy,
        }


# Compatibility Pydantic models for legacy callers
class ExecutionRequest(BaseModel):
    workspace: str
    command: list[str]
    timeout_seconds: int = 60
    env: dict[str, str] = Field(default_factory=dict)
    network_policy: NetworkPolicy = NetworkPolicy.NONE


class ExecutionResult(BaseModel):
    command: list[str]
    exit_code: int | None
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool
