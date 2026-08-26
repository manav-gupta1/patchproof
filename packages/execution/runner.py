from __future__ import annotations
from dataclasses import dataclass
import subprocess
import time


@dataclass(frozen=True, init=False)
class CommandResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float

    def __init__(
        self, command, stdout, stderr, *,
        returncode=None, exit_code=None,
        duration_seconds=None, duration_ms=None,
    ):
        if returncode is None:
            returncode = exit_code
        if returncode is None:
            raise TypeError("CommandResult requires returncode or exit_code")
        if duration_seconds is None:
            duration_seconds = (duration_ms / 1000.0) if duration_ms is not None else 0.0
        object.__setattr__(self, "command", tuple(command))
        object.__setattr__(self, "returncode", int(returncode))
        object.__setattr__(self, "stdout", stdout)
        object.__setattr__(self, "stderr", stderr)
        object.__setattr__(self, "duration_seconds", float(duration_seconds))

    @property
    def exit_code(self):
        return self.returncode

    @property
    def timed_out(self):
        return False

    @property
    def duration_ms(self):
        return int(self.duration_seconds * 1000)

    @property
    def succeeded(self):
        return self.returncode == 0

    @property
    def combined_output(self):
        return self.stdout + (("\n" + self.stderr) if self.stderr else "")


class ExecutionError(RuntimeError):
    pass


class SandboxCommandRunner:
    def __init__(self, cwd, timeout_seconds=900):
        self.cwd = cwd
        self.timeout_seconds = timeout_seconds

    def run(self, command, *, timeout_seconds=None):
        command = tuple(command)
        started = time.monotonic()
        try:
            proc = subprocess.run(
                command,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds or self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ExecutionError(
                f"command timed out after {timeout_seconds or self.timeout_seconds}s: {command}"
            ) from exc

        return CommandResult(
            command=command,
            returncode=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            duration_seconds=time.monotonic() - started,
        )
