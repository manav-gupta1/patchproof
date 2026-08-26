from pathlib import Path

import pytest

from packages.context.extractor import ContextExtractor
from packages.context.repo import RepoCheckout
from packages.context.limits import ContextBudget, enforce_context_budget


def test_context_extraction_uses_finding_location():
    repo = RepoCheckout(Path(__file__).resolve().parents[1] / "fixtures" / "vulnerable-python")
    finding = {
        "rule_id": "python.sql",
        "fingerprint": "fp",
        "path": "app.py",
        "start_line": 9,
        "end_line": 9,
        "severity": "high",
    }

    context = ContextExtractor(repo).extract(finding, context_lines=2)

    assert context.rule_id == "python.sql"
    assert context.code
    assert "sqlite" in "\n".join(context.imports).lower()
    assert any("test" in p.lower() for p in context.test_files)


def test_repository_path_traversal_is_blocked():
    repo = RepoCheckout(Path(__file__).resolve().parents[1])
    with pytest.raises(ValueError):
        repo.read_file("../../etc/passwd")


def test_context_budget_limits_lists_and_text():
    result = enforce_context_budget(
        {
            "code": "x" * 100,
            "before": "b" * 100,
            "after": "a" * 100,
            "imports": list(range(20)),
            "test_files": list(range(20)),
        },
        ContextBudget(max_file_bytes=10, max_imports=2, max_tests=3),
    )
    assert len(result["code"]) == 10
    assert len(result["imports"]) == 2
    assert len(result["test_files"]) == 3
