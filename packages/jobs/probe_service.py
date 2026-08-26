from __future__ import annotations


class ProbeService:
    """Combines liveness and readiness without conflating their meanings."""

    def __init__(self, health_probe, readiness_probe):
        self.health_probe = health_probe
        self.readiness_probe = readiness_probe

    def health(self):
        return self.health_probe.check()

    def readiness(self):
        return self.readiness_probe.check()

    def status(self):
        health = self.health()
        readiness = self.readiness()
        return {
            "healthy": health.healthy,
            "ready": readiness.ready,
            "health_checks": health.checks,
            "readiness_reason": readiness.reason,
        }
