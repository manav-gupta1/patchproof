from packages.verification.engine import VerificationEngine


class Sandbox:
    def __init__(self, passed=True):
        self.passed = passed

    def run(self, workspace, argv):
        from packages.sandbox.runner import SandboxResult
        return SandboxResult(self.passed, 0 if self.passed else 1, "ok", "")


def test_verification_requires_all_checks():
    engine = VerificationEngine(
        sandbox=Sandbox(True),
        test_command=["python", "-m", "pytest", "-q"],
        semgrep_command=["semgrep", "--config", "auto", "--error"],
    )
    result = engine.verify("/repo", [], {}, {"patch": "diff --git a/x b/x\n"})
    assert result.verified
    assert len(result.checks) == 3


def test_verification_fails_closed_on_sandbox_error():
    engine = VerificationEngine(
        sandbox=Sandbox(False),
        test_command=["python", "-m", "pytest", "-q"],
    )
    result = engine.verify("/repo", [], {}, {"patch": "diff --git a/x b/x\n"})
    assert not result.verified
