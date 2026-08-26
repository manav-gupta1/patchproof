from __future__ import annotations

import threading
from time import monotonic


class WorkerLifecycle:
    """Graceful lifecycle controller for long-running job workers."""

    def __init__(self, worker, poll_interval=1.0, on_error=None):
        if poll_interval <= 0:
            raise ValueError("poll_interval must be > 0")
        self.worker = worker
        self.poll_interval = poll_interval
        self.on_error = on_error
        self.stop_event = threading.Event()
        self.thread = None
        self.started = False
        self.draining = False

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.draining = False
        self.started = True

        def loop():
            while not self.stop_event.is_set():
                try:
                    if not self.draining:
                        self.worker.poll_once()
                except Exception as exc:
                    if self.on_error:
                        self.on_error(exc)
                finally:
                    self.stop_event.wait(self.poll_interval)

        self.thread = threading.Thread(
            target=loop, name="job-worker", daemon=True
        )
        self.thread.start()

    def drain(self):
        """Stop accepting new work while allowing in-flight work to finish."""
        self.draining = True
        if hasattr(self.worker, "begin_drain"):
            self.worker.begin_drain()

    def stop(self, timeout=30):
        """Drain, then stop the polling loop without abandoning in-flight work."""
        self.drain()
        if hasattr(self.worker, "wait_for_idle"):
            self.worker.wait_for_idle(timeout=timeout)
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=max(1, timeout))
        self.started = False

    def is_running(self):
        return bool(self.thread and self.thread.is_alive())
