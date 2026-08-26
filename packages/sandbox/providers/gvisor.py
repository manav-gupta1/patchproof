from __future__ import annotations

import subprocess
from packages.sandbox.models import SandboxUnavailableError
from packages.sandbox.providers.container import DockerContainerSandboxProvider


class GVisorSandboxProvider(DockerContainerSandboxProvider):
    """
    Hardened gVisor (runsc) container sandbox provider.
    Runs untrusted third-party repository code inside a gVisor user-space kernel sandbox.
    """

    def __init__(
        self,
        image: str = "patchproof/runner:latest",
        container_cli: str = "docker",
        runtime: str = "runsc",
        verify_runtime_available: bool = True,
    ) -> None:
        super().__init__(image=image, container_cli=container_cli, runtime=runtime)
        if verify_runtime_available:
            self._assert_runsc_available()

    @property
    def provider_name(self) -> str:
        return "gvisor"

    @property
    def runtime_name(self) -> str:
        return self.runtime or "runsc"

    def _assert_runsc_available(self) -> None:
        """Verify that runsc is configured in Docker runtimes."""
        try:
            res = subprocess.run(
                [self.container_cli, "info", "--format", "{{json .Runtimes}}"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if res.returncode == 0 and "runsc" in res.stdout:
                return
        except Exception:
            pass

        # Also check if runsc binary exists
        try:
            res = subprocess.run(["runsc", "--version"], capture_output=True, timeout=2, check=False)
            if res.returncode == 0:
                return
        except Exception:
            pass

        raise SandboxUnavailableError(
            f"gVisor runtime '{self.runtime}' is not installed or configured in Docker daemon. "
            f"Fail-closed: unsafe execution is prohibited."
        )
