from __future__ import annotations

import hashlib
import subprocess
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class CommandResult:
    argv: list[str]
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    stdout_sha256: str
    stderr_sha256: str

    @property
    def passed(self) -> bool:
        return self.exit_code == 0


class CommandExecutor:
    def __init__(self, cwd, timeout_seconds: int = 120):
        self.cwd = str(cwd)
        self.timeout_seconds = timeout_seconds

    def run(self, argv: list[str]) -> CommandResult:
        started = time.monotonic()
        try:
            proc = subprocess.run(
                argv,
                cwd=self.cwd,
                text=True,
                capture_output=True,
                timeout=self.timeout_seconds,
                check=False,
            )
            exit_code = proc.returncode
            stdout, stderr = proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as exc:
            exit_code = 124
            stdout = exc.stdout or ""
            stderr = (exc.stderr or "") + "\nTIMEOUT"
        duration_ms = int((time.monotonic() - started) * 1000)
        return CommandResult(
            argv=list(argv),
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
            stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),
            stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
        )
