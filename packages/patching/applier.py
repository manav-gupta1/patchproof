from __future__ import annotations

from pathlib import Path

from packages.patching.models import AppliedPatch, PatchCandidate, PatchStatus


class PatchApplyError(ValueError):
    pass


class PatchApplier:
    """Applies exact text replacements inside a repository.

    Exact matching prevents the model from silently modifying an unexpected location.
    """

    def apply(self, repository_root: str | Path, candidate: PatchCandidate) -> AppliedPatch:
        root = Path(repository_root).resolve()
        changed: list[str] = []

        for operation in candidate.operations:
            path = (root / operation.file).resolve()
            try:
                path.relative_to(root)
            except ValueError as exc:
                raise PatchApplyError(f"Patch path escapes repository root: {operation.file}") from exc

            if not path.is_file():
                raise PatchApplyError(f"Patch target does not exist: {operation.file}")

            text = path.read_text(encoding="utf-8")
            occurrences = text.count(operation.old_text)
            if occurrences != 1:
                raise PatchApplyError(
                    f"Expected exactly one match in {operation.file}, found {occurrences}"
                )

            path.write_text(text.replace(operation.old_text, operation.new_text, 1), encoding="utf-8")
            changed.append(operation.file)

        return AppliedPatch(
            candidate=candidate,
            status=PatchStatus.APPLIED,
            changed_files=changed,
        )
