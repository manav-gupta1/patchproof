from pathlib import Path

import pytest

from packages.context import ContextExtractor, ContextExtractionError
from packages.scanner import SemgrepAdapter


def test_context_rejects_path_escape(tmp_path: Path) -> None:
    finding = SemgrepAdapter().parse(
        {
            "results": [
                {
                    "check_id": "test.rule",
                    "path": "../secret.py",
                    "start": {"line": 1},
                    "extra": {"severity": "WARNING"},
                }
            ]
        }
    )[0]

    with pytest.raises(ContextExtractionError, match="escapes"):
        ContextExtractor().extract(tmp_path, finding)
