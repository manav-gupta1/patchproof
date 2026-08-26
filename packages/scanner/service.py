from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from packages.scanner.models import FindingLocation, NormalizedFinding
from packages.scanner.semgrep import SemgrepAdapter


class ScannerService:
    """Production scanner service running Semgrep with AST/heuristic fallback."""

    def __init__(self, semgrep_config: str = "auto") -> None:
        self.semgrep_config = semgrep_config
        self.adapter = SemgrepAdapter()

    def scan(self, workspace: str | Path) -> list[NormalizedFinding]:
        """Scan workspace and return normalized findings."""
        ws_path = Path(workspace).resolve()

        # 1. Attempt Semgrep scan if available
        findings = self._run_semgrep(ws_path)
        if findings:
            return findings

        # 2. Heuristic rule-based fallback scan
        return self._run_heuristic_scan(ws_path)

    def _run_semgrep(self, ws_path: Path) -> list[NormalizedFinding]:
        """Run Semgrep CLI and parse output."""
        try:
            cmd = [
                "semgrep",
                "scan",
                "--config",
                self.semgrep_config,
                "--json",
                "--metrics=off",
                "--disable-version-check",
                str(ws_path),
            ]
            proc = subprocess.run(
                cmd,
                cwd=ws_path,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            if proc.stdout:
                payload = json.loads(proc.stdout)
                return self.adapter.parse(payload)
        except Exception:
            pass
        return []

    def _run_heuristic_scan(self, ws_path: Path) -> list[NormalizedFinding]:
        """Rule-based scan across workspace files."""
        findings: list[NormalizedFinding] = []
        rule_patterns = [
            (
                "python.sql-injection",
                re.compile(r"SELECT\s+.*\s+FROM\s+.*\s+WHERE\s+.*\{.+\}", re.IGNORECASE),
                "HIGH",
                "Possible SQL injection via formatted query string",
                "python",
            ),
            (
                "python.command-injection",
                re.compile(r"(os\.system|subprocess\.Popen|subprocess\.run)\(.*shell=True.*\)", re.IGNORECASE),
                "HIGH",
                "Potential command injection with shell=True",
                "python",
            ),
            (
                "python.unsafe-eval",
                re.compile(r"\beval\(", re.IGNORECASE),
                "HIGH",
                "Use of dangerous built-in eval() function",
                "python",
            ),
        ]

        for file_path in ws_path.rglob("*.py"):
            if any(part.startswith((".", "__")) for part in file_path.parts):
                continue
            try:
                content = file_path.read_text()
            except Exception:
                continue

            rel_path = str(file_path.relative_to(ws_path))
            lines = content.splitlines()

            for line_idx, line in enumerate(lines, start=1):
                for rule_id, pattern, severity, message, language in rule_patterns:
                    if pattern.search(line):
                        fingerprint = f"{rule_id}:{rel_path}:{line_idx}"
                        findings.append(
                            NormalizedFinding(
                                fingerprint=fingerprint,
                                rule_id=rule_id,
                                severity=severity,
                                message=message,
                                language=language,
                                location=FindingLocation(
                                    file=rel_path,
                                    start_line=line_idx,
                                    end_line=line_idx,
                                    start_column=1,
                                    end_column=len(line) + 1,
                                ),
                                metadata={"snippet": line.strip()},
                                raw={"line": line, "rule": rule_id},
                                received_at=datetime.now(timezone.utc),
                            )
                        )

        return findings
