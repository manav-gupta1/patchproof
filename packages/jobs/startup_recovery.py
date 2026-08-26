from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StartupRecoveryReport:
    recovered: int
    completed: int


class StartupRecovery:
    """Run recovery before accepting new work after process startup."""

    def __init__(self, reconciler):
        self.reconciler = reconciler
        self.ready = False
        self.report = None

    def initialize(self, now=None):
        result = self.reconciler.reconcile(now=now)
        self.report = StartupRecoveryReport(
            recovered=len(result.get("recovered", [])),
            completed=len(result.get("completed", [])),
        )
        self.ready = True
        return self.report

    def require_ready(self):
        if not self.ready:
            raise RuntimeError("worker is not ready: startup recovery incomplete")
