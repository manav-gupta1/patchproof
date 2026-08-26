from packages.scanner import SemgrepAdapter


def test_normalizes_semgrep_result() -> None:
    payload = {
        "results": [
            {
                "check_id": "python.lang.security.audit.sql-injection",
                "path": "app.py",
                "start": {"line": 10, "col": 5},
                "end": {"line": 10, "col": 20},
                "extra": {
                    "message": "Possible SQL injection",
                    "severity": "WARNING",
                    "metadata": {"technology": ["python"], "cwe": ["CWE-89"]},
                },
            }
        ]
    }

    finding = SemgrepAdapter().parse(payload)[0]

    assert finding.rule_id == "python.lang.security.audit.sql-injection"
    assert finding.location.file == "app.py"
    assert finding.location.start_line == 10
    assert finding.language == "python"
    assert finding.metadata["cwe"] == ["CWE-89"]
    assert finding.raw["check_id"] == "python.lang.security.audit.sql-injection"
