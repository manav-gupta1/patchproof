from __future__ import annotations

import json

from packages.verification.executor import CommandExecutor


class SemgrepRunner:
    def __init__(self, executor: CommandExecutor, binary: str = "semgrep"):
        self.executor = executor
        self.binary = binary

    def run(self, targets: list[str] | None = None) -> dict:
        argv = [
            self.binary,
            "--config", "auto",
            "--json",
            "--no-git-ignore",
        ]
        argv.extend(targets or ["."])
        result = self.executor.run(argv)

        findings = []
        try:
            payload = json.loads(result.stdout or "{}")
            findings = payload.get("results", [])
        except json.JSONDecodeError:
            pass

        return {
            "result": result,
            "findings": findings,
            "finding_count": len(findings),
            "clean": len(findings) == 0 and result.exit_code in (0, 1),
        }
