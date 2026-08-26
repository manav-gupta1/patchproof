from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ContextBudget:
    max_file_bytes: int = 512_000
    max_context_lines: int = 60
    max_imports: int = 50
    max_tests: int = 100


def enforce_context_budget(context: dict, budget: ContextBudget) -> dict:
    result = dict(context)

    for key in ("code", "before", "after"):
        value = str(result.get(key, ""))
        result[key] = value[: budget.max_file_bytes]

    result["imports"] = list(result.get("imports", []))[: budget.max_imports]
    result["test_files"] = list(result.get("test_files", []))[: budget.max_tests]
    return result
