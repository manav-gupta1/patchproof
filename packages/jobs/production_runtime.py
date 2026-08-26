from __future__ import annotations

from dataclasses import dataclass

from .probe_service import ProbeService
from .startup_recovery import StartupRecovery
from .worker_bootstrap import WorkerBootstrap


@dataclass(frozen=True)
class RuntimeState:
    started: bool
    ready: bool


class ProductionRuntime:
    """Single composition root for recovery, worker lifecycle and probes."""

    def __init__(self, reconciler, lifecycle):
        self.startup_recovery = StartupRecovery(reconciler)
        self.lifecycle = lifecycle
        self.bootstrap = WorkerBootstrap(self.startup_recovery, lifecycle)
        self.probes = None
        self.started = False

    def start(self, now=None):
        report = self.bootstrap.start(now=now)
        self.probes = ProbeService(
            health_probe=_health_probe(self.lifecycle),
            readiness_probe=_readiness_probe(
                self.startup_recovery, self.lifecycle
            ),
        )
        self.started = True
        return report

    def stop(self, timeout=30):
        self.bootstrap.stop(timeout=timeout)
        self.started = False

    def state(self):
        ready = bool(self.probes and self.probes.readiness().ready)
        return RuntimeState(started=self.started, ready=ready)


def _health_probe(lifecycle):
    from .health import HealthProbe
    return HealthProbe(lifecycle)


def _readiness_probe(recovery, lifecycle):
    from .readiness import ReadinessProbe
    return ReadinessProbe(recovery, lifecycle)
