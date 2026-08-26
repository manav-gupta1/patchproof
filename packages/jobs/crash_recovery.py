from __future__ import annotations

class CrashRecovery:
    """Recovery boundary for jobs abandoned by a terminated worker."""

    def __init__(self, reconciler):
        self.reconciler = reconciler

    def recover(self, now=None):
        return self.reconciler.reconcile(now=now)
