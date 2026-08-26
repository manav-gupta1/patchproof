from __future__ import annotations

import threading


class RecoveryScheduler:
    def __init__(self, runner, interval_seconds=30, on_error=None):
        if interval_seconds < 1:
            raise ValueError("interval_seconds must be >= 1")
        self.runner = runner
        self.interval_seconds = interval_seconds
        self.on_error = on_error
        self.stop_event = threading.Event()
        self.thread = None

    def run_once(self, now=None):
        if hasattr(self.runner, "run_once"):
            return self.runner.run_once(now=now)
        if hasattr(self.runner, "reconcile"):
            return self.runner.reconcile(now=now)
        raise TypeError("recovery runner must expose run_once() or reconcile()")

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()

        def loop():
            while not self.stop_event.is_set():
                try:
                    self.run_once()
                except Exception as exc:
                    if self.on_error:
                        self.on_error(exc)
                finally:
                    self.stop_event.wait(self.interval_seconds)

        self.thread = threading.Thread(
            target=loop, name="recovery-reconciler", daemon=True
        )
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=max(2, self.interval_seconds + 1))
