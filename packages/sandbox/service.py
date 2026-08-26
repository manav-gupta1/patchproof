from __future__ import annotations
from packages.sandbox.bundle import WorkspaceBundle
from packages.sandbox.policy import SandboxPolicy
from packages.sandbox.runner import GVisorCommandRunner


class SandboxExecutionService:
    def __init__(self, runner=None, policy=None):
        self.runner = runner or GVisorCommandRunner()
        self.policy = policy or SandboxPolicy()

    def execute(self, repository, command):
        with WorkspaceBundle(repository) as bundle:
            return self.runner.run(
                bundle_dir=bundle,
                command=command,
                policy=self.policy,
            )
