from pathlib import Path

from packages.execution.pipeline import RealVerificationPipeline
from packages.sandbox.runner import SandboxResult


class FakeSandbox:
    def __init__(self):
        self.calls = []

    def execute(self, repository, command):
        self.calls.append((Path(repository), tuple(command)))
        if command[0] == "semgrep":
            return SandboxResult(True, 0, '{"results":[]}', "")
        return SandboxResult(True, 0, "24 passed in 0.1s", "")


def test_pipeline_executes_both_commands_through_sandbox():
    sandbox = FakeSandbox()
    result = RealVerificationPipeline(Path("."), sandbox=sandbox).run()

    assert len(sandbox.calls) == 2
    assert sandbox.calls[0][1] == ("semgrep", "--config", "auto", "--json", ".")
    assert sandbox.calls[1][1] == ("python", "-m", "pytest", "-q")
    assert result.verification.verified is True


def test_pipeline_does_not_use_direct_subprocess_runner():
    sandbox = FakeSandbox()
    pipeline = RealVerificationPipeline(Path("."), sandbox=sandbox)
    assert not hasattr(pipeline, "runner")
