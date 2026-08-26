from __future__ import annotations
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import time

from packages.sandbox.policy import SandboxPolicy


class SandboxError(RuntimeError):
    pass


@dataclass(frozen=True, init=False)
class SandboxResult:
    passed: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float

    def __init__(self, *args, **kwargs):
        # Preserve the historical contract:
        #   SandboxResult(passed, exit_code, stdout, stderr)
        # while also accepting the temporary runner contract:
        #   SandboxResult(returncode, stdout, stderr, duration_seconds)
        if kwargs:
            if "returncode" in kwargs:
                rc = int(kwargs["returncode"])
                object.__setattr__(self, "passed", rc == 0)
                object.__setattr__(self, "exit_code", rc)
                object.__setattr__(self, "stdout", kwargs.get("stdout", ""))
                object.__setattr__(self, "stderr", kwargs.get("stderr", ""))
                object.__setattr__(self, "duration_seconds", kwargs.get("duration_seconds", 0.0))
                return
            object.__setattr__(self, "passed", bool(kwargs["passed"]))
            object.__setattr__(self, "exit_code", int(kwargs["exit_code"]))
            object.__setattr__(self, "stdout", kwargs.get("stdout", ""))
            object.__setattr__(self, "stderr", kwargs.get("stderr", ""))
            object.__setattr__(self, "duration_seconds", kwargs.get("duration_seconds", 0.0))
            return

        if len(args) != 4:
            raise TypeError("SandboxResult expects four positional arguments")

        if isinstance(args[0], bool):
            passed, exit_code, stdout, stderr = args
            duration = 0.0
        elif isinstance(args[0], int) and isinstance(args[1], str):
            returncode, stdout, stderr, duration = args
            passed, exit_code = returncode == 0, returncode
        else:
            passed, exit_code, stdout, stderr = args
            duration = 0.0

        object.__setattr__(self, "passed", bool(passed))
        object.__setattr__(self, "exit_code", int(exit_code))
        object.__setattr__(self, "stdout", stdout)
        object.__setattr__(self, "stderr", stderr)
        object.__setattr__(self, "duration_seconds", float(duration))

    @property
    def argv(self):
        return self.command if hasattr(self, "command") else []

    @property
    def policy(self):
        return {"network": False}

    @property
    def returncode(self):
        return self.exit_code

    @property
    def succeeded(self):
        return self.exit_code == 0

    @property
    def combined_output(self):
        return self.stdout + (("\n" + self.stderr) if self.stderr else "")


class GVisorCommandRunner:
    '''
    Host-side boundary for an external runsc/gVisor launcher.

    The application never executes repository commands directly. The launcher
    is responsible for entering the isolated sandbox and applying the policy.
    '''

    def __init__(self, sandbox_launcher: str = "runsc"):
        self.sandbox_launcher = sandbox_launcher

    def build_command(self, *, bundle_dir: Path, command, policy: SandboxPolicy):
        policy.validate()
        command = tuple(command)
        if not command:
            raise SandboxError("empty command")

        # Explicit flags make the security contract visible to the launcher.
        return (
            self.sandbox_launcher,
            "do",
            "--network=none",
            f"--pids-limit={policy.pids_limit}",
            f"--memory-limit={policy.memory_mb}m",
            f"--cpu-limit={policy.cpu_seconds}",
            "--rootfs=readonly",
            str(bundle_dir),
            "--",
            *command,
        )

    def run(self, workspace=None, command=None, *, bundle_dir=None, policy=None):
        bundle_dir = Path(bundle_dir or workspace)
        command = command or ()
        policy = policy or SandboxPolicy()
        argv = self.build_command(
            bundle_dir=bundle_dir, command=command, policy=policy
        )
        started = time.monotonic()
        try:
            proc = subprocess.run(
                argv,
                cwd=bundle_dir,
                capture_output=True,
                text=True,
                timeout=policy.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise SandboxError(
                f"sandbox command exceeded {policy.timeout_seconds}s"
            ) from exc
        except OSError as exc:
            raise SandboxError("sandbox launcher could not be started") from exc

        return SandboxResult(
            returncode=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            duration_seconds=time.monotonic() - started,
        )


class DockerSandboxRunner:
    """Docker container sandbox runner with security isolation."""

    def __init__(
        self,
        image: str = "python:3.12-slim",
        timeout: int = 300,
        policy: SandboxPolicy | None = None,
        container_cli: str = "docker",
    ):
        self.image = image
        self.timeout = timeout
        self.policy = policy or SandboxPolicy(timeout_seconds=timeout)
        self.container_cli = container_cli

    def _build_docker_command(self, workspace: str | Path, argv: tuple[str, ...] | list[str]) -> list[str]:
        ws_path = str(Path(workspace).resolve())
        return [
            self.container_cli,
            "run",
            "--rm",
            "--network=none",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            f"--pids-limit={self.policy.pids_limit}",
            f"--memory={self.policy.memory_mb}m",
            "-v",
            f"{ws_path}:/workspace:rw",
            "-w",
            "/workspace",
            self.image,
            *argv,
        ]

    def run(self, workspace: str | Path, argv: tuple[str, ...] | list[str]) -> SandboxResult:
        from packages.github.auth import sanitize_secret_text
        cmd = self._build_docker_command(workspace, argv)
        started = time.monotonic()
        try:
            proc = subprocess.run(
                cmd,
                text=True,
                capture_output=True,
                timeout=self.policy.timeout_seconds,
                check=False,
            )
            stdout = sanitize_secret_text(proc.stdout[:self.policy.max_output_bytes])
            stderr = sanitize_secret_text(proc.stderr[:self.policy.max_output_bytes])
            return SandboxResult(
                proc.returncode == 0,
                proc.returncode,
                stdout,
                stderr,
            )
        except subprocess.TimeoutExpired as exc:
            return SandboxResult(
                False,
                124,
                sanitize_secret_text(exc.stdout or ""),
                sanitize_secret_text((exc.stderr or "") + "\nSANDBOX TIMEOUT"),
            )
        except Exception as exc:
            return SandboxResult(
                False,
                1,
                "",
                sanitize_secret_text(f"Docker sandbox failure: {exc}"),
            )





class SandboxRunner:
    """Repository-oriented adapter used by the vertical/e2e layer.

    ``runtime="local"`` is intentionally opt-in for deterministic tests and
    development only. Production callers should use the gVisor command runner
    through :class:`SandboxExecutionService`.
    """

    def __init__(self, workspace, policy=None, *, runtime="runsc"):
        self.workspace = Path(workspace).resolve()
        self.policy = policy or SandboxPolicy()
        self.runtime = runtime
        self.policy.validate()

    def run(self, command):
        if self.runtime == "local":
            if os.environ.get("PATCHPROOF_ALLOW_LOCAL_SANDBOX") != "1":
                raise RuntimeError("local sandbox requires PATCHPROOF_ALLOW_LOCAL_SANDBOX=1")
            started = time.monotonic()
            try:
                proc = subprocess.run(
                    tuple(command), cwd=self.workspace, capture_output=True,
                    text=True, timeout=self.policy.timeout_seconds, check=False,
                )
                result = SandboxResult(proc.returncode == 0, proc.returncode, proc.stdout, proc.stderr)
            except subprocess.TimeoutExpired as exc:
                result = SandboxResult(False, 124, exc.stdout or "", (exc.stderr or "") + "\nSANDBOX TIMEOUT")
            object.__setattr__(result, "duration_seconds", time.monotonic() - started)
            return result
        if self.runtime != "runsc":
            raise ValueError(f"unknown sandbox runtime: {self.runtime}")
        return GVisorCommandRunner().run(
            bundle_dir=self.workspace, command=command, policy=self.policy
        )

    def run_tests(self):
        return self.run(("python", "-m", "pytest", "-q"))

    def run_semgrep(self):
        result = self.run(("semgrep", "--config", "auto", "--json", "."))
        import json
        try:
            payload = json.loads(result.stdout)
            finding_count = len(payload.get("results", []))
        except (json.JSONDecodeError, TypeError, AttributeError):
            finding_count = -1
        return {"finding_count": finding_count, "output": result.stdout, "stderr": result.stderr, "exit_code": result.exit_code}


# Compatibility name used by the verification/orchestration layer.
LocalSandboxRunner = GVisorCommandRunner
