from __future__ import annotations

from pathlib import Path

from packages.patching.models import FindingContext


class ContextExtractor:
    """Builds a bounded model context from a Semgrep finding."""

    def __init__(self, max_excerpt_chars: int = 16000) -> None:
        self.max_excerpt_chars = max_excerpt_chars

    def extract(
        self,
        *,
        workspace: str,
        fingerprint: str,
        rule_id: str,
        path: str,
        start_line: int,
        end_line: int,
        severity: str,
    ) -> FindingContext:
        root = Path(workspace).resolve()
        target = (root / path).resolve()

        if root not in target.parents and target != root:
            raise ValueError("finding path escapes workspace")
        if not target.is_file():
            raise FileNotFoundError(path)

        lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        start = max(0, start_line - 1)
        end = min(len(lines), max(end_line, start_line) + 40)
        excerpt = "\n".join(
            f"{i + 1}: {lines[i]}" for i in range(start, end)
        )[: self.max_excerpt_chars]

        symbols: list[str] = []
        for line in lines[max(0, start - 40):min(len(lines), end + 40)]:
            stripped = line.strip()
            if stripped.startswith(("def ", "async def ", "class ", "function ")):
                symbols.append(stripped[:300])

        project_files = [
            str(p.relative_to(root))
            for p in root.rglob("*")
            if p.is_file() and ".git" not in p.parts
        ][:500]

        return FindingContext(
            fingerprint=fingerprint,
            rule_id=rule_id,
            path=path,
            start_line=start_line,
            end_line=end_line,
            severity=severity,
            source_excerpt=excerpt,
            related_symbols=symbols,
            project_files=project_files,
        )
