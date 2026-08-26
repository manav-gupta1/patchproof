from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMConfig:
    base_url: str
    api_key: str
    triage_model: str
    reasoning_model: str
    timeout_seconds: float = 60
    max_retries: int = 2

    @classmethod
    def from_env(cls) -> "LLMConfig":
        return cls(
            base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
            api_key=os.getenv("LLM_API_KEY", ""),
            triage_model=os.getenv("LLM_TRIAGE_MODEL", ""),
            reasoning_model=os.getenv("LLM_REASONING_MODEL", ""),
            timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "60")),
            max_retries=int(os.getenv("LLM_MAX_RETRIES", "2")),
        )
