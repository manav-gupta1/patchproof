from pathlib import Path

from packages.execution.pipeline import RealVerificationPipeline
from packages.execution.runner import CommandResult


class FakeRunner:
    def __init__(self):
        self.commands = []

    def execute(self, repository, command):
        self.commands.append(tuple(command))
        if command[0] == "semgrep":
            return CommandResult(tuple(command), '{"results":[]}', "", returncode=0, duration_seconds=0.1)
        return CommandResult(tuple(command), "24 passed in 0.1s", "", returncode=0, duration_seconds=0.1)


def test_pipeline_uses_real_execution_boundaries():
    runner = FakeRunner()
    result = RealVerificationPipeline(Path("."), runner).run()

    assert runner.commands[0][0] == "semgrep"
    assert runner.commands[1] == ("python", "-m", "pytest", "-q")
    assert result.scanner.findings == 0
    assert result.tests.passed == 24
    assert result.verification.verified is True
    assert result.execution_evidence.evidence_sha256


def test_failed_test_execution_fails_verification():
    class FailingRunner(FakeRunner):
        def execute(self, repository, command):
            self.commands.append(tuple(command))
            if command[0] == "semgrep":
                return CommandResult(tuple(command), '{"results":[]}', "", returncode=0, duration_seconds=0.1)
            return CommandResult(tuple(command), "1 failed, 23 passed", "", returncode=1, duration_seconds=0.1)

    result = RealVerificationPipeline(Path("."), FailingRunner()).run()
    assert result.verification.verified is False
