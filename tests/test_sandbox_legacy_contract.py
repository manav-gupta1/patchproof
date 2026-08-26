from packages.sandbox.runner import SandboxResult


def test_success_contract():
    result = SandboxResult(True, 0, "ok", "")
    assert result.passed is True
    assert result.exit_code == 0
    assert result.returncode == 0


def test_failure_contract():
    result = SandboxResult(False, 7, "", "failed")
    assert result.passed is False
    assert result.exit_code == 7
    assert result.returncode == 7
