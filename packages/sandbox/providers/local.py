from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Any, Sequence

from packages.github.auth import sanitize_secret_text
from packages.sandbox.environment import build_isolated_environment
from packages.sandbox.models import (
    NetworkPolicy,
    SandboxRequest,
    SandboxResult,
    SandboxSecurityError,
)
from packages.sandbox.provider import SandboxProvider


class LocalProcessSandboxProvider(SandboxProvider):
    """
    Deterministic local process sandbox for unit testing and local development.
    Applies strict environment allowlisting, timeout enforcement, output bounds,
    and secret redaction.
    """

    def __init__(self, allow_network: bool = False) -> None:
        self.allow_network = allow_network

    @property
    def provider_name(self) -> str:
        return "local"

    @property
    def runtime_name(self) -> str:
        return "process"

    def _normalize_request(self, request_or_ws: Any, command: Any = None, **kwargs: Any) -> SandboxRequest:
        if isinstance(request_or_ws, SandboxRequest):
            return request_or_ws
        if command is None and hasattr(request_or_ws, "command"):
            # ExecutionRequest legacy model
            return SandboxRequest(
                command=request_or_ws.command,
                workspace_path=request_or_ws.workspace,
                timeout_seconds=getattr(request_or_ws, "timeout_seconds", 60),
                environment=getattr(request_or_ws, "env", None),
            )
        ws = request_or_ws
        cmd = command
        timeout = kwargs.get("timeout", kwargs.get("timeout_seconds", 60.0))
        env = kwargs.get("env", kwargs.get("environment", None))
        max_bytes = kwargs.get("max_output_bytes", 100 * 1024)
        return SandboxRequest(
            command=cmd,
            workspace_path=ws,
            timeout_seconds=float(timeout),
            environment=env,
            max_output_bytes=int(max_bytes),
        )

    def run(self, request: SandboxRequest | Any, command: Any = None, **kwargs: Any) -> SandboxResult:
        req = self._normalize_request(request, command=command, **kwargs)
        ws_path = Path(req.workspace_path).resolve()
        if not ws_path.exists():
            raise FileNotFoundError(f"Workspace directory '{ws_path}' does not exist")

        # Network check
        if req.network_policy in (NetworkPolicy.RESTRICTED, "restricted") and not self.allow_network:
            # Structure failure for restricted network request when disabled
            return SandboxResult(
                exit_code=1,
                stdout="",
                stderr="Sandbox security error: network access is disabled by policy",
                duration_seconds=0.0,
                provider=self.provider_name,
                runtime=self.runtime_name,
                network_policy=str(req.network_policy),
                command=req.cmd_list,
            )

        env = build_isolated_environment(custom_env=req.environment, base_env=os.environ)

        cmd = req.cmd_list
        started = time.monotonic()
        timed_out = False
        resource_limited = False
        raw_stdout = ""
        raw_stderr = ""
        exit_code = 0

        try:
            proc = subprocess.run(
                cmd,
                cwd=ws_path,
                env=env,
                capture_output=True,
                text=True,
                timeout=req.timeout_seconds,
                check=False,
            )
            exit_code = proc.returncode
            raw_stdout = proc.stdout or ""
            raw_stderr = proc.stderr or ""
            if exit_code in (137, 139):  # SIGKILL (e.g. OOM) or SIGSEGV
                resource_limited = True
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            exit_code = 124
            raw_stdout = exc.stdout or ""
            raw_stderr = (exc.stderr or "") + "\nSANDBOX TIMEOUT"
        except Exception as exc:
            exit_code = 1
            raw_stderr = f"Sandbox execution error: {exc}"

        duration = time.monotonic() - started

        # Truncate output
        orig_size = len(raw_stdout) + len(raw_stderr)
        max_bytes = req.max_output_bytes
        truncated = orig_size > max_bytes

        stdout_trunc = raw_stdout[:max_bytes]
        remaining = max(0, max_bytes - len(stdout_trunc))
        stderr_trunc = raw_stderr[:remaining]

        # Sanitize any accidental secrets
        clean_stdout = sanitize_secret_text(stdout_trunc)
        clean_stderr = sanitize_secret_text(stderr_trunc)
        captured_size = len(clean_stdout) + len(clean_stderr)

        return SandboxResult(
            exit_code=exit_code,
            stdout=clean_stdout,
            stderr=clean_stderr,
            duration_seconds=duration,
            timed_out=timed_out,
            resource_limited=resource_limited,
            output_truncated=truncated,
            original_output_size=orig_size,
            captured_output_size=captured_size,
            provider=self.provider_name,
            runtime=self.runtime_name,
            network_policy=str(req.network_policy),
            command=cmd,
        )
