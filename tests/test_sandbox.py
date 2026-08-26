from pathlib import Path
import pytest
from packages.sandbox.executor import SandboxExecutor
from packages.sandbox.policy import SandboxPolicy

def test_policy_disables_network():
    with pytest.raises(ValueError):
        SandboxPolicy(network=True).validate()

def test_policy_has_security_limits():
    p=SandboxPolicy()
    assert p.pids > 0 and p.memory_mb >= 128 and p.timeout_seconds > 0

def test_command_is_hardened():
    ex=SandboxExecutor(Path("/tmp/repo"), Path("/tmp/workspace"), runtime="runsc")
    argv=ex._docker_argv(["pytest","-q"])
    assert argv[argv.index("--network")+1] == "none"
    assert "--read-only" in argv
    assert argv[argv.index("--cap-drop")+1] == "ALL"
    assert argv[argv.index("--runtime")+1] == "runsc"
    assert any("dst=/repo,readonly" in x for x in argv)
    assert any("dst=/workspace,rw" in x for x in argv)
