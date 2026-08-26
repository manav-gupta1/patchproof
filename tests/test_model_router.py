import pytest

from packages.agents import (
    ModelRoute,
    ModelRouter,
    StaticLLMProvider,
    VulnerabilityAnalysis,
)


def _provider() -> StaticLLMProvider:
    return StaticLLMProvider(
        VulnerabilityAnalysis(
            finding_fingerprint="abc",
            classification="test",
            confidence=0.9,
            eligible=True,
            attack_hypothesis="test",
            reasoning="test",
        )
    )


def test_router_selects_reasoning_route() -> None:
    provider = _provider()
    router = ModelRouter(
        triage=ModelRoute("cheap", provider, "triage-model", "classification"),
        reasoning=ModelRoute("strong", provider, "reasoning-model", "analysis"),
    )

    route = router.route("reasoning")

    assert route.name == "strong"
    assert route.model == "reasoning-model"


def test_router_rejects_unknown_route() -> None:
    provider = _provider()
    router = ModelRouter(
        triage=ModelRoute("cheap", provider, "triage-model", "classification"),
        reasoning=ModelRoute("strong", provider, "reasoning-model", "analysis"),
    )

    with pytest.raises(ValueError):
        router.route("exploit")
