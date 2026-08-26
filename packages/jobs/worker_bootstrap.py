from __future__ import annotations


class WorkerBootstrap:
    """Order startup so recovery completes before polling begins."""

    def __init__(self, startup_recovery, lifecycle):
        self.startup_recovery = startup_recovery
        self.lifecycle = lifecycle

    def start(self, now=None):
        report = self.startup_recovery.initialize(now=now)
        self.lifecycle.start()
        return report

    def stop(self, timeout=30):
        self.lifecycle.stop(timeout=timeout)
