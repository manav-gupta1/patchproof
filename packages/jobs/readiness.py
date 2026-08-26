from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReadinessStatus:
    ready: bool
    reason: str


class ReadinessProbe:
    """Expose a deterministic readiness decision for process orchestration."""

    def __init__(self, startup_recovery, lifecycle):
        self.startup_recovery = startup_recovery
        self.lifecycle = lifecycle

    def check(self):
        if not self.startup_recovery.ready:
            return ReadinessStatus(False, "startup_recovery_incomplete")
        if not self.lifecycle.is_running():
            return ReadinessStatus(False, "worker_not_running")
        if getattr(self.lifecycle, "draining", False):
            return ReadinessStatus(False, "worker_draining")
        return ReadinessStatus(True, "ready")
