from __future__ import annotations
from pathlib import Path


class TreeSitterContext:
    """Best-effort structural context extractor with bounded source windows."""

    def __init__(self, max_bytes=12000):
        self.max_bytes = max_bytes

    def extract(self, workspace, finding):
        path = finding.get("path")
        if not path:
            return {"path": None, "source": "", "language": None}
        file = (Path(workspace) / path).resolve()
        root = Path(workspace).resolve()
        if root not in file.parents and file != root:
            raise ValueError("finding path escapes workspace")
        if not file.is_file():
            raise FileNotFoundError(path)
        raw = file.read_bytes()[:self.max_bytes]
        text = raw.decode("utf-8", errors="replace")
        return {
            "path": path,
            "language": file.suffix.lstrip("."),
            "start_line": finding.get("start_line"),
            "end_line": finding.get("end_line"),
            "source": text,
        }
