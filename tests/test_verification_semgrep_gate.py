import json

from packages.sandbox.models import ExecutionRequest, ExecutionResult
from packages.verification.models import VerificationPlan
from packages.verification.runner import VerificationRunner


class FakeSandbox:
    def __init__(self, results):
        self.results = list(results)
        self.i = 0

    def run(self, request: ExecutionRequest) -> ExecutionResult:
        assert isinstance(request, ExecutionRequest)
        result = self.results[self.i]
        self.i += 1
        return result


def _result(exit_code: int, stdout: str = "", stderr: str = "") -> ExecutionResult:
    return ExecutionResult(
        command=["fake"],
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        duration_ms=1,
        timed_out=False,
    )


def _plan() -> VerificationPlan:
    return VerificationPlan(
        baseline_exploit=["poc"],
        patched_exploit=["poc"],
        test_command=["pytest"],
        semgrep_command=["semgrep"],
        finding_fingerprint="fixture-sqli-001",
    )


def test_verification_does_not_accept_semgrep_scanner_error() -> None:
    sandbox = FakeSandbox([
        _result(0),
        _result(1),
        _result(0, "passed"),
        _result(2, "", "scanner crashed"),
    ])

    result = VerificationRunner(sandbox=sandbox).run("/repo", _plan())

    assert result.verified is False
    assert result.semgrep_exit_code == 2
    assert result.semgrep_clean is False


def test_verification_accepts_semgrep_json_zero_findings() -> None:
    sandbox = FakeSandbox([
        _result(0),
        _result(1),
        _result(0, "passed"),
        _result(0, json.dumps({"results": [], "errors": []})),
    ])

    result = VerificationRunner(sandbox=sandbox).run("/repo", _plan())

    assert result.verified is True
    assert result.semgrep_exit_code == 0
    assert result.semgrep_finding_count == 0
    assert result.semgrep_clean is True
