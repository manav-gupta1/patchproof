from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from packages.sandbox.factory import get_sandbox_provider
from packages.sandbox.models import SandboxRequest, SandboxResult
from packages.sandbox.provider import SandboxProvider


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    resource_limited: bool = False


@dataclass(frozen=True)
class VerificationResult:
    verified: bool
    checks: tuple[CheckResult, ...]
    evidence_id: str
    sandbox_provider: str = "unknown"
    sandbox_runtime: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "verified": self.verified,
            "checks": [asdict(x) for x in self.checks],
            "evidence_id": self.evidence_id,
            "sandbox_provider": self.sandbox_provider,
            "sandbox_runtime": self.sandbox_runtime,
        }


class VerificationEngine:
    def __init__(
        self,
        *,
        sandbox: SandboxProvider | Any = None,
        test_command: tuple[str, ...] | list[str] | str | None = None,
        semgrep_command: tuple[str, ...] | list[str] | str | None = None,
    ) -> None:
        self.sandbox = sandbox or get_sandbox_provider()
        self.test_command = test_command
        self.semgrep_command = semgrep_command

    def verify(
        self,
        workspace: str | Path,
        findings: list[Any],
        proposal: dict[str, Any],
        patch_result: dict[str, Any],
    ) -> VerificationResult:
        checks: list[CheckResult] = []
        sbx_provider = getattr(self.sandbox, "provider_name", "sandbox")
        sbx_runtime = getattr(self.sandbox, "runtime_name", "runtime")

        if self.test_command:
            cmd = [self.test_command] if isinstance(self.test_command, str) else list(self.test_command)
            req = SandboxRequest(command=cmd, workspace_path=workspace)
            if hasattr(self.sandbox, "run"):
                try:
                    r = self.sandbox.run(req)
                except TypeError:
                    r = self.sandbox.run(workspace, cmd)
            else:
                r = self.sandbox(workspace, cmd)

            checks.append(
                CheckResult(
                    name="tests",
                    passed=getattr(r, "passed", getattr(r, "exit_code", 1) == 0),
                    exit_code=getattr(r, "exit_code", None),
                    stdout=getattr(r, "stdout", ""),
                    stderr=getattr(r, "stderr", ""),
                    timed_out=getattr(r, "timed_out", False),
                    resource_limited=getattr(r, "resource_limited", False),
                )
            )

        if self.semgrep_command:
            cmd = [self.semgrep_command] if isinstance(self.semgrep_command, str) else list(self.semgrep_command)
            req = SandboxRequest(command=cmd, workspace_path=workspace)
            if hasattr(self.sandbox, "run"):
                try:
                    r = self.sandbox.run(req)
                except TypeError:
                    r = self.sandbox.run(workspace, cmd)
            else:
                r = self.sandbox(workspace, cmd)

            checks.append(
                CheckResult(
                    name="semgrep_rescan",
                    passed=getattr(r, "passed", getattr(r, "exit_code", 1) == 0),
                    exit_code=getattr(r, "exit_code", None),
                    stdout=getattr(r, "stdout", ""),
                    stderr=getattr(r, "stderr", ""),
                    timed_out=getattr(r, "timed_out", False),
                    resource_limited=getattr(r, "resource_limited", False),
                )
            )

        checks.append(CheckResult(name="patch_applied", passed=bool(patch_result.get("patch"))))

        verified = bool(checks) and all(x.passed for x in checks)
        material = json.dumps(
            {
                "findings": findings,
                "proposal": proposal,
                "patch": patch_result,
                "checks": [asdict(x) for x in checks],
            },
            sort_keys=True,
            default=str,
        ).encode("utf-8")
        evidence_id = f"ev-{sha256(material).hexdigest()[:16]}"

        return VerificationResult(
            verified=verified,
            checks=tuple(checks),
            evidence_id=evidence_id,
            sandbox_provider=sbx_provider,
            sandbox_runtime=sbx_runtime,
        )
