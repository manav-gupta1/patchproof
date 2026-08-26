from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

from packages.sandbox import SandboxExecutor


class SemgrepStatus(str, Enum):
    NO_FINDINGS = "no_findings"
    FINDINGS_PRESENT = "findings_present"
    SCANNER_ERROR = "scanner_error"
    INVALID_CONFIG = "invalid_config"
    TIMEOUT = "timeout"
    INVALID_OUTPUT = "invalid_output"


@dataclass(frozen=True)
class SemgrepVerification:
    status: SemgrepStatus
    passed: bool
    findings_count: int
    exit_code: int
    stdout: str
    stderr: str
    error: str | None = None


class SemgrepVerifier:
    """Semgrep-specific verification.

    Exit codes are never interpreted as "clear" by themselves. JSON output is
    authoritative when available; operational failures remain failures.
    """

    def __init__(self, sandbox: SandboxExecutor) -> None:
        self.sandbox = sandbox

    async def verify(
        self,
        *,
        repository_path: str,
        command: list[str],
    ) -> SemgrepVerification:
        result = self.sandbox.run(command)

        if result.timed_out:
            return SemgrepVerification(
                status=SemgrepStatus.TIMEOUT,
                passed=False,
                findings_count=0,
                exit_code=result.exit_code,
                stdout=result.stdout,
                stderr=result.stderr,
                error="Semgrep execution timed out",
            )

        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            status = (
                SemgrepStatus.INVALID_CONFIG
                if self._looks_like_config_error(result.stderr)
                else SemgrepStatus.SCANNER_ERROR
            )
            return SemgrepVerification(
                status=status,
                passed=False,
                findings_count=0,
                exit_code=result.exit_code,
                stdout=result.stdout,
                stderr=result.stderr,
                error=f"Semgrep did not return valid JSON: {exc}",
            )

        if not isinstance(payload, dict):
            return SemgrepVerification(
                status=SemgrepStatus.INVALID_OUTPUT,
                passed=False,
                findings_count=0,
                exit_code=result.exit_code,
                stdout=result.stdout,
                stderr=result.stderr,
                error="Semgrep JSON root must be an object",
            )

        results = payload.get("results")
        if not isinstance(results, list):
            return SemgrepVerification(
                status=SemgrepStatus.INVALID_OUTPUT,
                passed=False,
                findings_count=0,
                exit_code=result.exit_code,
                stdout=result.stdout,
                stderr=result.stderr,
                error="Semgrep JSON did not contain a results array",
            )

        findings = len(results)
        if findings > 0:
            return SemgrepVerification(
                status=SemgrepStatus.FINDINGS_PRESENT,
                passed=False,
                findings_count=findings,
                exit_code=result.exit_code,
                stdout=result.stdout,
                stderr=result.stderr,
            )

        # A syntactically valid JSON report with zero findings is the only
        # condition that passes the security gate.
        return SemgrepVerification(
            status=SemgrepStatus.NO_FINDINGS,
            passed=True,
            findings_count=0,
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    @staticmethod
    def _looks_like_config_error(stderr: str) -> bool:
        text = stderr.lower()
        return any(
            marker in text
            for marker in (
                "invalid rule",
                "invalid configuration",
                "yaml parse",
                "unknown field",
                "no such file or directory",
            )
        )
