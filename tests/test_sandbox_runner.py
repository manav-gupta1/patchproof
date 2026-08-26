from pathlib import Path
import os
import pytest

from packages.sandbox.runner import SandboxRunner, SandboxPolicy


def test_local_sandbox_requires_explicit_opt_in(tmp_path, monkeypatch):
    monkeypatch.delenv("PATCHPROOF_ALLOW_LOCAL_SANDBOX", raising=False)
    runner = SandboxRunner(tmp_path, SandboxPolicy(timeout_seconds=1), runtime="local")
    with pytest.raises(RuntimeError):
        runner.run(("python", "-c", "print('x')"))


def test_local_sandbox_runs_when_explicitly_enabled(tmp_path, monkeypatch):
    monkeypatch.setenv("PATCHPROOF_ALLOW_LOCAL_SANDBOX", "1")
    runner = SandboxRunner(tmp_path, SandboxPolicy(timeout_seconds=2), runtime="local")
    result = runner.run(("python", "-c", "print('sandbox-ok')"))
    assert result.passed
    assert "sandbox-ok" in result.stdout
    assert result.policy["network"] is False


def test_unknown_runtime_fails_closed(tmp_path):
    runner = SandboxRunner(tmp_path, runtime="unknown-runtime")
    with pytest.raises(ValueError):
        runner.run(("python", "-c", "print('x')"))
