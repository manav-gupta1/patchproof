from pathlib import Path
import pytest

from packages.agents import AnalystAgent, AnalystRequest, StaticLLMProvider, VulnerabilityAnalysis
from packages.context import ContextExtractor
from packages.scanner import SemgrepAdapter


@pytest.mark.asyncio
async def test_analyst_returns_structured_analysis(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text(
        "def load(user_id):\n    query = f'SELECT * FROM users WHERE id={user_id}'\n    return execute(query)\n",
        encoding="utf-8",
    )
    finding = SemgrepAdapter().parse({"results": [{
        "check_id": "python.sql-injection", "path": "app.py", "start": {"line": 2},
        "extra": {"severity": "ERROR", "message": "Possible SQL injection", "metadata": {"technology": ["python"]}},
    }]})[0]
    context = ContextExtractor().extract(tmp_path, finding)
    expected = VulnerabilityAnalysis(
        finding_fingerprint=finding.fingerprint, classification="sql_injection", confidence=0.91,
        eligible=True, source="user_id", sink="execute(query)",
        attack_hypothesis="An attacker-controlled user_id reaches a SQL execution sink without parameterization.",
        reasoning="The context shows an interpolated value passed to execute.", relevant_files=["app.py"],
    )
    result = await AnalystAgent(StaticLLMProvider(expected)).analyze(AnalystRequest(finding=finding, context=context))
    assert result.classification == "sql_injection"
    assert result.eligible
