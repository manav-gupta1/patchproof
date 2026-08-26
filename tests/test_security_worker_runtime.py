from packages.security.findings import parse_semgrep_json
from packages.verification.engine import VerificationEngine
from packages.verification.fixture_runner import FixtureRunner


def test_semgrep_finding_is_normalized_with_stable_fingerprint():
    payload = {
        "results": [{
            "check_id": "python.sql-injection",
            "path": "app.py",
            "start": {"line": 10},
            "end": {"line": 10},
            "extra": {"severity": "ERROR", "message": "unsafe SQL"},
        }]
    }
    finding = parse_semgrep_json(payload)[0]
    assert finding.rule_id == "python.sql-injection"
    assert finding.path == "app.py"
    assert len(finding.fingerprint) == 64


def test_verification_requires_all_security_gates():
    finding = parse_semgrep_json({
        "results": [{
            "check_id": "x", "path": "app.py",
            "start": {"line": 1}, "end": {"line": 1},
            "extra": {"severity": "ERROR"},
        }]
    })[0]

    class Sandbox:
        def __init__(self, tests_pass=True, semgrep_pass=True):
            self.tests_pass = tests_pass
            self.semgrep_pass = semgrep_pass

        def run(self, workspace, command):
            from packages.sandbox.runner import SandboxResult
            if command[0] == "semgrep":
                return SandboxResult(self.semgrep_pass, 0 if self.semgrep_pass else 1, "", "")
            return SandboxResult(self.tests_pass, 0 if self.tests_pass else 1, "", "")

    good = VerificationEngine(
        sandbox=Sandbox(),
        test_command=["python", "-m", "pytest", "-q"],
        semgrep_command=["semgrep", "--config", "auto", "--error"],
    ).verify("/repo", [finding], {"diff": "fix"}, {"patch": "diff --git a/app.py b/app.py\n"})
    assert good.verified

    semgrep_bad = VerificationEngine(
        sandbox=Sandbox(semgrep_pass=False),
        test_command=["python", "-m", "pytest", "-q"],
        semgrep_command=["semgrep", "--config", "auto", "--error"],
    ).verify("/repo", [finding], {"diff": "fix"}, {"patch": "diff --git a/app.py b/app.py\n"})
    assert not semgrep_bad.verified

    patch_bad = VerificationEngine(
        sandbox=Sandbox(),
        test_command=["python", "-m", "pytest", "-q"],
        semgrep_command=["semgrep", "--config", "auto", "--error"],
    ).verify("/repo", [finding], {"diff": "fix"}, {})
    assert not patch_bad.verified
