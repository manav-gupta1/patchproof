from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import random


class FailureClass(str, Enum):
    RETRYABLE = "retryable"
    PERMANENT = "permanent"


class RetryableJobError(RuntimeError):
    pass


class PermanentJobError(RuntimeError):
    pass


@dataclass(frozen=True)
class RetryDecision:
    failure_class: FailureClass
    retry: bool
    delay_seconds: float
    reason: str


class RetryPolicy:
    def __init__(self, max_attempts=5, base_delay=5.0, max_delay=300.0, jitter=0.2):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter

    def classify(self, exc):
        if isinstance(exc, PermanentJobError):
            return FailureClass.PERMANENT
        if isinstance(exc, (ValueError, TypeError)):
            return FailureClass.PERMANENT
        return FailureClass.RETRYABLE

    def decide(self, exc, attempt):
        kind = self.classify(exc)
        if kind == FailureClass.PERMANENT:
            return RetryDecision(kind, False, 0.0, str(exc))

        if attempt >= self.max_attempts:
            return RetryDecision(
                kind, False, 0.0,
                f"retry budget exhausted at attempt {attempt}"
            )

        raw = min(self.max_delay, self.base_delay * (2 ** max(0, attempt - 1)))
        delay = raw * (1 + random.uniform(-self.jitter, self.jitter))
        return RetryDecision(kind, True, max(0.0, delay), str(exc))
