from __future__ import annotations

from pathlib import Path

from packages.patching.models import PatchCandidate


class PatchApplyError(ValueError):
    pass


class PatchApplier:
    """Apply exact text replacements with repository-boundary validation."""

    def apply(self, repository_root: str | Path, candidate: PatchCandidate):
        root = Path(repository_root).resolve()
        changed: list[str] = []

        if isinstance(candidate, dict):
            patch_text = candidate.get("patch")
            if patch_text:
                return self._apply_unified_diff(root, patch_text)
            files = candidate.get("files", {})
            operations = []
            for filename, new_text in files.items():
                path = (root / filename).resolve()
                try:
                    path.relative_to(root)
                except ValueError as exc:
                    raise PatchApplyError(
                        f"Patch path escapes repository root: {filename}"
                    ) from exc
                if not path.is_file():
                    raise PatchApplyError(
                        f"Patch target does not exist: {filename}"
                    )
                operations.append(type("_PatchOp", (), {
                    "file": filename,
                    "old_text": path.read_text(encoding="utf-8"),
                    "new_text": new_text,
                })())
        else:
            operations = list(candidate.operations)
        if not operations and candidate.files:
            # Deterministic/reference providers may supply complete-file
            # replacements. Convert that canonical legacy field into the same
            # bounded application path rather than silently ignoring it.
            for filename, new_text in candidate.files.items():
                path = (root / filename).resolve()
                try:
                    path.relative_to(root)
                except ValueError as exc:
                    raise PatchApplyError(
                        f"Patch path escapes repository root: {filename}"
                    ) from exc
                if not path.is_file():
                    raise PatchApplyError(
                        f"Patch target does not exist: {filename}"
                    )
                old_text = path.read_text(encoding="utf-8")
                operations.append(
                    type("_PatchOp", (), {
                        "file": filename,
                        "old_text": old_text,
                        "new_text": new_text,
                    })()
                )

        for operation in operations:
            path = (root / operation.file).resolve()
            try:
                path.relative_to(root)
            except ValueError as exc:
                raise PatchApplyError(
                    f"Patch path escapes repository root: {operation.file}"
                ) from exc

            if not path.is_file():
                raise PatchApplyError(
                    f"Patch target does not exist: {operation.file}"
                )

            text = path.read_text(encoding="utf-8")
            occurrences = text.count(operation.old_text)
            if occurrences != 1:
                raise PatchApplyError(
                    f"Expected exactly one match in {operation.file}, found {occurrences}"
                )

            path.write_text(
                text.replace(operation.old_text, operation.new_text, 1),
                encoding="utf-8",
            )
            changed.append(operation.file)

        return changed

    def _apply_unified_diff(self, root: Path, patch_text: str):
        import re

        lines = patch_text.splitlines()
        i = 0
        changed = []
        while i < len(lines):
            if not lines[i].startswith("--- "):
                i += 1
                continue
            old_path = lines[i][4:].split("\t", 1)[0]
            i += 1
            if i >= len(lines) or not lines[i].startswith("+++ "):
                raise PatchApplyError("Malformed unified diff")
            new_path = lines[i][4:].split("\t", 1)[0]
            rel = new_path[2:] if new_path.startswith("b/") else new_path
            if rel == "/dev/null":
                rel = old_path[2:] if old_path.startswith("a/") else old_path
            path = (root / rel).resolve()
            try:
                path.relative_to(root)
            except ValueError as exc:
                raise PatchApplyError(f"Patch path escapes repository root: {rel}") from exc
            if not path.is_file():
                raise PatchApplyError(f"Patch target does not exist: {rel}")
            i += 1

            old = path.read_text(encoding="utf-8").splitlines(keepends=True)
            out = []
            pos = 0
            while i < len(lines) and not lines[i].startswith("--- "):
                if not lines[i].startswith("@@"):
                    i += 1
                    continue
                m = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", lines[i])
                if not m:
                    raise PatchApplyError("Malformed unified diff hunk")
                old_start = int(m.group(1)) - 1
                out.extend(old[pos:old_start])
                pos = old_start
                i += 1
                while i < len(lines) and not lines[i].startswith("@@") and not lines[i].startswith("--- "):
                    line = lines[i]
                    if line == "\\ No newline at end of file":
                        i += 1
                        continue
                    if not line:
                        i += 1
                        continue
                    marker, content = line[0], line[1:]
                    if marker == " ":
                        if pos >= len(old) or old[pos].rstrip("\n") != content:
                            raise PatchApplyError(f"Unified diff context mismatch in {rel}")
                        out.append(old[pos]); pos += 1
                    elif marker == "-":
                        if pos >= len(old) or old[pos].rstrip("\n") != content:
                            raise PatchApplyError(f"Unified diff removal mismatch in {rel}")
                        pos += 1
                    elif marker == "+":
                        out.append(content + "\n")
                    else:
                        raise PatchApplyError("Malformed unified diff line")
                    i += 1
            out.extend(old[pos:])
            path.write_text("".join(out), encoding="utf-8")
            changed.append(rel)
        if not changed:
            raise PatchApplyError("Unified diff contained no file changes")
        return changed
