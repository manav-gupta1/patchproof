from __future__ import annotations
import json
import subprocess


class SemgrepScanner:
    def __init__(self, config="auto", timeout=120):
        self.config = config
        self.timeout = timeout

    def scan(self, workspace):
        proc = subprocess.run(
            ["semgrep", "--config", self.config, "--json", "--quiet", "."],
            cwd=workspace, text=True, capture_output=True, timeout=self.timeout,
        )
        if proc.returncode not in (0, 1):
            raise RuntimeError(f"Semgrep failed: {proc.stderr[-1000:]}")
        data = json.loads(proc.stdout or "{}")
        return data.get("results", [])
