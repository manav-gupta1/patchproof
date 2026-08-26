from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import ast


class ContextExtractionError(ValueError):
    pass


@dataclass(frozen=True)
class CodeContext:
    path: str
    source: str
    start_line: int
    end_line: int
    symbol: str | None
    related_tests: tuple[str, ...]
    rule_id: str | None = None
    fingerprint: str | None = None
    severity: str | None = None
    code: str = ""
    imports: tuple[str, ...] = ()
    test_files: tuple[str, ...] = ()


class ContextExtractor:
    def __init__(self, repository: Path | None = None, max_lines=240):
        if repository is not None and not isinstance(repository, (str, Path)):
            repository = getattr(repository, "root", getattr(repository, "path", repository))
        self.repository = Path(repository) if repository is not None else None
        self.max_lines = max_lines

    def extract(self, repository_or_finding, finding=None, context_lines=None) -> CodeContext:
        # Supports both:
        #   ContextExtractor(repo).extract(finding, context_lines=2)
        # and:
        #   ContextExtractor().extract(repo, finding)
        if finding is None:
            if self.repository is None:
                raise TypeError("repository is required")
            repository = self.repository
            finding = repository_or_finding
        else:
            repository = Path(repository_or_finding)

        if hasattr(finding, "location"):
            values = {
                "path": finding.location.file,
                "start_line": finding.location.start_line,
                "end_line": finding.location.end_line,
                "rule_id": finding.rule_id,
                "fingerprint": finding.fingerprint,
                "severity": finding.severity,
            }
            get = lambda key, default=None: values.get(key, default)
        elif hasattr(finding, "model_dump"):
            values = finding.model_dump()
            get = lambda key, default=None: values.get(key, default)
        elif hasattr(finding, "path"):
            get = lambda key, default=None: getattr(finding, key, default)
        else:
            get = lambda key, default=None: finding.get(key, default)
        rel = Path(get("path"))
        path = (repository / rel).resolve()
        repository_root = repository.resolve()
        try:
            path.relative_to(repository_root)
        except ValueError as exc:
            raise ContextExtractionError(f"path {rel} escapes repository") from exc
        source = path.read_text()
        lines = source.splitlines()
        start = max(1, int(get("start_line", 1)))
        end = min(len(lines), int(get("end_line", start)))

        if context_lines is not None:
            radius = int(context_lines)
            lo = max(1, start - radius)
            hi = min(len(lines), end + radius)
        else:
            lo = max(1, start - self.max_lines // 2)
            hi = min(len(lines), end + self.max_lines // 2)

        snippet = "\n".join(lines[lo-1:hi])

        symbol = None
        if path.suffix == ".py":
            try:
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        if getattr(node, "lineno", 0) <= start <= getattr(node, "end_lineno", 0):
                            symbol = node.name
                            break
            except SyntaxError:
                pass

        imports = []
        if path.suffix == ".py":
            try:
                tree = ast.parse(source)
                for node in tree.body:
                    if isinstance(node, ast.Import):
                        imports.extend(ast.unparse(x) for x in node.names)
                    elif isinstance(node, ast.ImportFrom):
                        imports.append(ast.unparse(node))
            except SyntaxError:
                pass

        tests = []
        for candidate in repository.rglob("test_*.py"):
            tests.append(str(candidate.relative_to(repository)))
            if len(tests) >= 20:
                break

        return CodeContext(
            str(rel), snippet, lo, hi, symbol, tuple(tests),
            get("rule_id"), get("fingerprint"), get("severity"),
            snippet, tuple(imports), tuple(tests)
        )
