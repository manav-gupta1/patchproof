from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from time import monotonic


@dataclass
class RecoveryMetrics:
    runs: int = 0
    recovered: int = 0
    completed: int = 0
    failures: int = 0
    last_duration_seconds: float = 0.0
    _lock: Lock = field(default_factory=Lock, repr=False)

    def observe(self, result, duration_seconds):
        with self._lock:
            self.runs += 1
            self.recovered += len(result.get("recovered", []))
            self.completed += len(result.get("completed", []))
            self.last_duration_seconds = duration_seconds

    def observe_failure(self, duration_seconds):
        with self._lock:
            self.runs += 1
            self.failures += 1
            self.last_duration_seconds = duration_seconds

    def snapshot(self):
        with self._lock:
            return {
                "runs": self.runs,
                "recovered": self.recovered,
                "completed": self.completed,
                "failures": self.failures,
                "last_duration_seconds": self.last_duration_seconds,
            }


class RecoveryRunObserver:
    def __init__(self, reconciler, metrics):
        self.reconciler = reconciler
        self.metrics = metrics

    def run_once(self, now=None):
        started = monotonic()
        try:
            result = self.reconciler.reconcile(now=now)
        except Exception:
            self.metrics.observe_failure(monotonic() - started)
            raise
        self.metrics.observe(result, monotonic() - started)
        return result
