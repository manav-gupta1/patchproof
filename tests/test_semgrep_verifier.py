import json

import pytest

from packages.sandbox import CommandResult, SandboxExecutor, ExecutionRequest
from packages.scanning import SemgrepStatus, SemgrepVerifier


class FakeSandbox(SandboxExecutor):
    def __init__(self, result: CommandResult) -> None:
        self.result = result

    def run(self, argv) -> CommandResult:
        return self.result


@pytest.mark.asyncio
async def test_zero_findings_is_the_only_clear_state() -> None:
    result = CommandResult(
        exit_code=0,
        stdout=json.dumps({"results": [], "errors": []}),
        stderr="",
        duration_ms=10,
        command=["semgrep", "--json"],
    )

    verification = await SemgrepVerifier(FakeSandbox(result)).verify(
        repository_path="/repo",
        command=["semgrep", "--json"],
    )

    assert verification.status is SemgrepStatus.NO_FINDINGS
    assert verification.passed is True


@pytest.mark.asyncio
async def test_findings_fail_even_with_zero_exit_code() -> None:
    result = CommandResult(
        exit_code=0,
        stdout=json.dumps({"results": [{"check_id": "test.rule"}]}),
        stderr="",
        duration_ms=10,
        command=["semgrep", "--json"],
    )

    verification = await SemgrepVerifier(FakeSandbox(result)).verify(
        repository_path="/repo",
        command=["semgrep", "--json"],
    )

    assert verification.status is SemgrepStatus.FINDINGS_PRESENT
    assert verification.passed is False
    assert verification.findings_count == 1


@pytest.mark.asyncio
async def test_invalid_json_is_scanner_failure() -> None:
    result = CommandResult(
        exit_code=2,
        stdout="not json",
        stderr="scanner crashed",
        duration_ms=10,
        command=["semgrep", "--json"],
    )

    verification = await SemgrepVerifier(FakeSandbox(result)).verify(
        repository_path="/repo",
        command=["semgrep", "--json"],
    )

    assert verification.status is SemgrepStatus.SCANNER_ERROR
    assert verification.passed is False


@pytest.mark.asyncio
async def test_config_error_is_distinguished() -> None:
    result = CommandResult(
        exit_code=2,
        stdout="",
        stderr="invalid rule: bad yaml",
        duration_ms=10,
        command=["semgrep", "--json"],
    )

    verification = await SemgrepVerifier(FakeSandbox(result)).verify(
        repository_path="/repo",
        command=["semgrep", "--json"],
    )

    assert verification.status is SemgrepStatus.INVALID_CONFIG
    assert verification.passed is False
