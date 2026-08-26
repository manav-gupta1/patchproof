import os
import pytest

from packages.llm.safety import LLMOutputGuard
from packages.llm.router import LLMRouter


def test_llm_guard_rejects_non_diff():
    with pytest.raises(ValueError):
        LLMOutputGuard().validate_patch({"patch": "rm -rf /"})


def test_llm_guard_accepts_unified_diff():
    p = {"patch": "diff --git a/x.py b/x.py\n--- a/x.py\n+++ b/x.py\n"}
    assert LLMOutputGuard().validate_patch(p) == p


def test_router_uses_injected_providers():
    calls = []
    router = LLMRouter(
        triage=lambda x: calls.append(("triage", x)) or {"relevant": True},
        reasoning=lambda x: calls.append(("reasoning", x)) or {"patch": "diff --git a/x b/x\n"},
    )
    router.triage_finding({"id": 1})
    router.generate_patch({}, {"id": 1})
    assert [x[0] for x in calls] == ["triage", "reasoning"]
