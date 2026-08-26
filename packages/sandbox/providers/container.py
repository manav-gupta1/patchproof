from __future__ import annotations

import os
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Sequence

from packages.github.auth import sanitize_secret_text
from packages.sandbox.environment import build_isolated_environment
from packages.sandbox.models import (
    NetworkPolicy,
    SandboxError,
    SandboxRequest,
    SandboxResult,
    SandboxUnavailableError,
)
from packages.sandbox.provider import SandboxProvider


class DockerContainerSandboxProvider(SandboxProvider):
    """
    Production Docker container sandbox provider using hardened container runtime.
    Applies non-root user, read-only base rootfs, isolated workspace volume,
    dropped capabilities, no-new-privileges, strict resource limits, network denial,
    and output bounds.
    """

    def __init__(
        self,
        image: str = "patchproof/runner:latest",
        container_cli: str = "docker",
        runtime: str | None = None,
    ) -> None:
        self.image = image
        self.container_cli = container_cli
        self.runtime = runtime

    @property
    def provider_name(self) -> str:
        return "container"

    @property
    def runtime_name(self) -> str:
        return self.runtime or "runc"

    def _normalize_request(self, request_or_ws: Any, command: Any = None, **kwargs: Any) -> SandboxRequest:
        if isinstance(request_or_ws, SandboxRequest):
            return request_or_ws
        if command is None and hasattr(request_or_ws, "command"):
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

    def _build_docker_argv(self, req: SandboxRequest, sandbox_id: str, ws_path: Path) -> list[str]:
        cmd = [
            self.container_cli,
            "run",
            "--rm",
            f"--name={sandbox_id}",
            f"--user={req.non_root_uid}:{req.non_root_uid}",
            "--read-only",
            "--tmpfs=/tmp:rw,noexec,nosuid,size=64m",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            f"--pids-limit={req.pids_limit}",
            f"--memory={req.memory_limit_mb}m",
            f"--memory-swap={req.memory_limit_mb}m",
            f"--cpus={req.cpu_limit}",
            "-v",
            f"{ws_path}:/workspace:rw",
            "-w",
            "/workspace",
        ]

        if self.runtime:
            cmd.insert(3, f"--runtime={self.runtime}")

        # Network isolation
        if req.network_policy in (NetworkPolicy.DENY, NetworkPolicy.NONE, "deny", "none"):
            cmd.append("--network=none")
        elif req.network_policy in (NetworkPolicy.RESTRICTED, "restricted"):
            cmd.append("--network=none")

        # Isolated environment variables
        isolated_env = build_isolated_environment(custom_env=req.environment)
        for k, v in isolated_env.items():
            cmd.extend(["-e", f"{k}={v}"])

        cmd.append(self.image)
        cmd.extend(req.cmd_list)
        return cmd

    def run(self, request: SandboxRequest | Any, command: Any = None, **kwargs: Any) -> SandboxResult:
        req = self._normalize_request(request, command=command, **kwargs)
        ws_path = Path(req.workspace_path).resolve()
        if not ws_path.exists():
            raise FileNotFoundError(f"Workspace directory '{ws_path}' does not exist")

        sandbox_id = f"patchproof-sbx-{uuid.uuid4().hex[:12]}"
        docker_cmd = self._build_docker_argv(req, sandbox_id, ws_path)

        started = time.monotonic()
        timed_out = False
        resource_limited = False
        raw_stdout = ""
        raw_stderr = ""
        exit_code = 0

        try:
            proc = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=req.timeout_seconds,
                check=False,
            )
            exit_code = proc.returncode
            raw_stdout = proc.stdout or ""
            raw_stderr = proc.stderr or ""
            if exit_code in (137, 139):  # SIGKILL (OOM or resource-killed) or SIGSEGV
                resource_limited = True
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            exit_code = 124
            raw_stdout = exc.stdout or ""
            raw_stderr = (exc.stderr or "") + "\nSANDBOX TIMEOUT"
            # Explicit cleanup of running container
            try:
                subprocess.run(
                    [self.container_cli, "rm", "-f", sandbox_id],
                    capture_output=True,
                    timeout=5,
                    check=False,
                )
            except Exception:
                pass
        except FileNotFoundError:
            raise SandboxUnavailableError(f"Container CLI '{self.container_cli}' is not installed or available on host PATH")
        except Exception as exc:
            exit_code = 1
            raw_stderr = f"Container sandbox error: {exc}"
        finally:
            # Guarantee container cleanup
            try:
                subprocess.run(
                    [self.container_cli, "rm", "-f", sandbox_id],
                    capture_output=True,
                    timeout=5,
                    check=False,
                )
            except Exception:
                pass

        duration = time.monotonic() - started

        # Truncate output
        orig_size = len(raw_stdout) + len(raw_stderr)
        max_bytes = req.max_output_bytes
        truncated = orig_size > max_bytes

        stdout_trunc = raw_stdout[:max_bytes]
        remaining = max(0, max_bytes - len(stdout_trunc))
        stderr_trunc = raw_stderr[:remaining]

        # Redact secrets
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
            sandbox_id=sandbox_id,
            network_policy=str(req.network_policy),
            command=req.cmd_list,
        )
