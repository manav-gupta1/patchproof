from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    workspace = Path(sys.argv[1])
    config = workspace / "semgrep.yml"
    if shutil.which("semgrep") is None:
        print(json.dumps({"available": False, "results": [], "error": "semgrep not installed"}))
        return 2

    proc = subprocess.run(
        ["semgrep", "--config", str(config), "--json", "--quiet", str(workspace)],
        text=True,
        capture_output=True,
        timeout=120,
    )
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        print(json.dumps({
            "available": True,
            "results": [],
            "error": proc.stderr[-4000:],
            "raw_exit": proc.returncode,
        }))
        return 3

    print(json.dumps(data))
    return 0 if proc.returncode in (0, 1) else proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
