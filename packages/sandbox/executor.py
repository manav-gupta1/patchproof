from __future__ import annotations
import hashlib
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from packages.sandbox.policy import SandboxPolicy
from packages.sandbox.models import ExecutionRequest

@dataclass(frozen=True)
class SandboxResult:
    argv: list[str]
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool
    sandboxed: bool
    stdout_sha256: str
    stderr_sha256: str

class SandboxExecutor:
    """Container execution boundary; production uses gVisor/runsc."""
    def __init__(self, repository: Path, workspace: Path, *,
                 image="patchproof/runner:latest", runtime="runsc",
                 policy=None, container_cli="docker"):
        self.repository = Path(repository).resolve()
        self.workspace = Path(workspace).resolve()
        self.image = image
        self.runtime = runtime
        self.policy = policy or SandboxPolicy()
        self.container_cli = container_cli
        self.policy.validate()

    def _docker_argv(self, argv: list[str]) -> list[str]:
        command = [
            self.container_cli, "run", "--rm",
            "--runtime", self.runtime,
            "--network", "none",
            "--read-only",
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "--pids-limit", str(self.policy.pids),
            "--memory", f"{self.policy.memory_mb}m",
            "--cpus", "1",
            "--mount", f"type=bind,src={self.repository},dst=/repo,readonly",
            "--mount", f"type=bind,src={self.workspace},dst=/workspace,rw",
            "--workdir", "/workspace",
            self.image,
        ]
        return command + argv

    def run(self, argv) -> SandboxResult:
        if isinstance(argv, ExecutionRequest):
            request = argv
            argv = request.command
        started = time.monotonic()
        command = self._docker_argv(argv)
        timed_out = False
        try:
            proc = subprocess.run(command, text=True, capture_output=True,
                                  timeout=self.policy.timeout_seconds, check=False)
            exit_code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as exc:
            timed_out, exit_code = True, 124
            stdout, stderr = exc.stdout or "", (exc.stderr or "") + "\nSANDBOX TIMEOUT"
        stdout = stdout[:self.policy.max_output_bytes]
        stderr = stderr[:self.policy.max_output_bytes]
        return SandboxResult(
            argv=command, exit_code=exit_code, stdout=stdout, stderr=stderr,
            duration_ms=int((time.monotonic()-started)*1000),
            timed_out=timed_out, sandboxed=True,
            stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),
            stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
        )
