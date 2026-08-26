from packages.verification.engine import VerificationEngine


class Sandbox:
    def __init__(self, passed=True):
        self.passed = passed
        self.calls = []

    def run(self, workspace, argv):
        from packages.sandbox.runner import SandboxResult
        self.calls.append(argv)
        return SandboxResult(self.passed, 0 if self.passed else 1, "ok", "")


def test_verification_requires_all_checks():
    sandbox = Sandbox(True)
    engine = VerificationEngine(
        sandbox=sandbox,
        test_command=["pytest", "-q"],
        semgrep_command=["semgrep", "--config", "auto", "--error"],
    )
    result = engine.verify(
        "/repo", [], {}, {"patch": "diff --git a/x b/x\n"}
    )
    assert result.verified is True
    assert result.evidence_id
    assert len(result.checks) == 3


def test_failed_sandbox_means_unverified():
    sandbox = Sandbox(False)
    engine = VerificationEngine(
        sandbox=sandbox,
        test_command=["pytest", "-q"],
    )
    result = engine.verify("/repo", [], {}, {"patch": "diff --git a/x b/x\n"})
    assert result.verified is False
