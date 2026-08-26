import pytest

from packages.agents import (
    AnalystRequest,
    AnalystService,
    ModelRoute,
    ModelRouter,
    StaticLLMProvider,
    VulnerabilityAnalysis,
)
from packages.context import RepositoryContext, SourceSpan
from packages.scanner.models import FindingLocation, NormalizedFinding


@pytest.mark.asyncio
async def test_analyst_service_records_model_metadata() -> None:
    finding = NormalizedFinding(
        fingerprint="abc",
        rule_id="test.rule",
        severity="WARNING",
        message="test",
        language="python",
        location=FindingLocation(
            file="app.py",
            start_line=1,
            start_column=1,
            end_line=1,
            end_column=5,
        ),
        metadata={},
        raw={},
    )
    context = RepositoryContext(
        repository_root="/repo",
        language="python",
        file="app.py",
        finding_span=SourceSpan(start_line=1, end_line=1),
        source="x = 1",
    )
    expected = VulnerabilityAnalysis(
        finding_fingerprint="abc",
        classification="test",
        confidence=0.9,
        eligible=True,
        attack_hypothesis="test",
        reasoning="test",
    )
    provider = StaticLLMProvider(expected)
    router = ModelRouter(
        triage=ModelRoute("cheap", provider, "triage-model", "classification"),
        reasoning=ModelRoute("strong", provider, "reasoning-model", "analysis"),
    )

    result, metadata = await AnalystService(router).analyze(
        AnalystRequest(finding=finding, context=context)
    )

    assert result == expected
    assert metadata.route == "strong"
    assert metadata.model == "reasoning-model"
    assert metadata.success is True
    assert metadata.request_id
