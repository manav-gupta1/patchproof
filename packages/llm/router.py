from __future__ import annotations
import json


class LLMRouter:
    """Provider-neutral routing boundary. Provider calls are injected."""

    def __init__(self, *, triage, reasoning):
        self.triage = triage
        self.reasoning = reasoning

    def triage_finding(self, finding):
        return self.triage(finding)

    def generate_patch(self, context, finding):
        result = self.reasoning({
            "finding": finding,
            "context": context,
            "instruction": (
                "Return a minimal security patch proposal. "
                "Do not claim verification. Do not execute code."
            ),
        })
        if isinstance(result, str):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {"patch": result}
        return result
