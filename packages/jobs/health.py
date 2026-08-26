from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HealthStatus:
    healthy: bool
    checks: dict[str, bool]


class HealthProbe:
    """Liveness probe independent from readiness."""

    def __init__(self, lifecycle):
        self.lifecycle = lifecycle

    def check(self):
        running = bool(self.lifecycle.is_running())
        return HealthStatus(healthy=running, checks={"process_running": running})
