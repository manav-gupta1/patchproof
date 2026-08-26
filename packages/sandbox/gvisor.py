from __future__ import annotations

from pathlib import Path
from typing import Any
from packages.sandbox.policy import SandboxPolicy
from packages.sandbox.runner import DockerSandboxRunner, SandboxResult


class GVisorSandboxRunner(DockerSandboxRunner):
    """
    Production gVisor sandbox adapter.

    Requires Docker configured with the gVisor `runsc` runtime. The runtime
    must be installed/configured by the host image; this class deliberately
    does not attempt privileged runtime installation from application code.
    """

    def __init__(
        self,
        image: str = "python:3.12-slim",
        timeout: int = 300,
        runtime: str = "runsc",
        policy: SandboxPolicy | None = None,
        container_cli: str = "docker",
    ):
        super().__init__(
            image=image,
            timeout=timeout,
            policy=policy,
            container_cli=container_cli,
        )
        self.runtime = runtime

    def _build_docker_command(self, workspace: str | Path, argv: tuple[str, ...] | list[str]) -> list[str]:
        base_cmd = super()._build_docker_command(workspace, argv)
        # Inject --runtime <runtime> after `docker run --rm`
        return [base_cmd[0], base_cmd[1], base_cmd[2], "--runtime", self.runtime] + base_cmd[3:]
