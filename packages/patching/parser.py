from __future__ import annotations

import re


class UnifiedDiffParser:
    FILE_RE = re.compile(r"^\+\+\+ b/(.+)$")

    def changed_files(self, diff: str) -> list[str]:
        files = []
        for line in diff.splitlines():
            match = self.FILE_RE.match(line)
            if match and match.group(1) not in files:
                files.append(match.group(1))
        return files

    def validate(self, diff: str) -> None:
        lines = diff.splitlines()
        if not any(line.startswith("diff --git ") for line in lines):
            raise ValueError("not a git unified diff")
        if not any(line.startswith("@@ ") for line in lines):
            raise ValueError("diff has no hunks")
        for path in self.changed_files(diff):
            if path.startswith("/") or ".." in path.split("/"):
                raise ValueError(f"unsafe patch path: {path}")
