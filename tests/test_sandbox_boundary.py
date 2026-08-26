from pathlib import Path
import pytest

from packages.sandbox.policy import SandboxPolicy, SandboxPolicyError
from packages.sandbox.runner import GVisorCommandRunner


def test_policy_is_fail_closed():
    policy = SandboxPolicy()
    policy.validate()
    assert policy.network_enabled is False
    assert policy.readonly_root is True


def test_network_cannot_be_enabled():
    with pytest.raises(SandboxPolicyError):
        SandboxPolicy(network_enabled=True).validate()


def test_writable_root_cannot_be_enabled():
    with pytest.raises(SandboxPolicyError):
        SandboxPolicy(readonly_root=False).validate()


def test_command_contains_isolation_flags():
    runner = GVisorCommandRunner("/usr/bin/runsc")
    argv = runner.build_command(
        bundle_dir=Path("/tmp/bundle"),
        command=("python", "-m", "pytest", "-q"),
        policy=SandboxPolicy(),
    )
    assert "--network=none" in argv
    assert "--rootfs=readonly" in argv
    assert any(x.startswith("--memory-limit=") for x in argv)
    assert any(x.startswith("--pids-limit=") for x in argv)
    assert argv[-3:] == ("python", "-m", "pytest") or argv[-4:] == ("python", "-m", "pytest", "-q")


def test_empty_command_rejected():
    with pytest.raises(Exception):
        GVisorCommandRunner().build_command(
            bundle_dir=Path("/tmp/b"),
            command=(),
            policy=SandboxPolicy(),
        )
