from __future__ import annotations

import signal
import threading


class ProcessShutdown:
    """Maps OS termination signals to a graceful worker drain/stop."""

    def __init__(self, lifecycle, stop_timeout=30):
        self.lifecycle = lifecycle
        self.stop_timeout = stop_timeout
        self._shutdown_once = threading.Event()
        self._previous = {}

    def install(self):
        for sig in (signal.SIGTERM, signal.SIGINT):
            self._previous[sig] = signal.getsignal(sig)
            signal.signal(sig, self._handle)

    def uninstall(self):
        for sig, handler in self._previous.items():
            signal.signal(sig, handler)
        self._previous.clear()

    def _handle(self, signum, frame):
        if self._shutdown_once.is_set():
            return
        self._shutdown_once.set()
        self.lifecycle.stop(timeout=self.stop_timeout)

    def shutdown(self):
        self._handle(signal.SIGTERM, None)
