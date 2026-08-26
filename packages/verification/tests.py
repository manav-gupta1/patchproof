from __future__ import annotations

from dataclasses import dataclass

from packages.sandbox import ExecutionRequest, LocalSandboxRunner, ResourceLimits


@dataclass
class TestRun:
    passed: bool
    exit_code: int | None
    stdout: str
    stderr: str
    command: list[str]


class TestAdapter:
    def __init__(self, runner: LocalSandboxRunner | None = None) -> None:
        self.runner = runner or LocalSandboxRunner()

    def run(
        self,
        workspace: str,
        *,
        command: list[str],
        timeout_seconds: int = 300,
    ) -> TestRun:
        result = self.runner.run(
            ExecutionRequest(
                workspace=workspace,
                command=command,
                limits=ResourceLimits(timeout_seconds=timeout_seconds),
            )
        )
        return TestRun(
            passed=result.status.value == "passed",
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            command=result.command,
        )
