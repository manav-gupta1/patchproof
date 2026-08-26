from __future__ import annotations

import json
import re
from pathlib import Path


class LocalSemgrepFixtureRunner:
    """Deterministic fixture runner used only when Semgrep is unavailable."""
    def __init__(self, repo):
        self.repo = Path(repo)

    def run(self, targets=None):
        path = self.repo / "app.py"
        text = path.read_text()
        vulnerable = bool(re.search(
            r"""['"]select role from users where name = ['"][^\n]*%s""",
            text,
        ))
        findings = [{
            "check_id": "python.sql-string-format",
            "path": "app.py",
            "start": {"line": 14},
            "end": {"line": 14},
            "extra": {"severity": "ERROR"},
        }] if vulnerable else []
        payload = {"results": findings, "errors": []}
        return {
            "result": type("Result", (), {
                "argv": ["local-semgrep-fixture"],
                "exit_code": 0,
                "stdout": json.dumps(payload),
                "stderr": "",
                "duration_ms": 1,
                "stdout_sha256": "fixture",
                "stderr_sha256": "fixture",
            })(),
            "findings": findings,
            "finding_count": len(findings),
            "clean": not findings,
        }
