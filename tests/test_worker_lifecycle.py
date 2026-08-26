import threading
import time

from packages.jobs.worker_lifecycle import WorkerLifecycle


class Worker:
    def __init__(self):
        self.polls = 0
        self.draining = False
        self.idle_waited = False

    def poll_once(self):
        self.polls += 1

    def begin_drain(self):
        self.draining = True

    def wait_for_idle(self, timeout=30):
        self.idle_waited = True


def test_start_and_stop_are_clean():
    w=Worker()
    lifecycle=WorkerLifecycle(w, poll_interval=0.01)
    lifecycle.start()
    time.sleep(0.03)
    lifecycle.stop(timeout=1)
    assert w.polls > 0
    assert w.draining is True
    assert w.idle_waited is True
    assert lifecycle.is_running() is False


def test_drain_stops_new_polls():
    w=Worker()
    lifecycle=WorkerLifecycle(w, poll_interval=0.01)
    lifecycle.start()
    time.sleep(0.02)
    before=w.polls
    lifecycle.drain()
    time.sleep(0.03)
    lifecycle.stop(timeout=1)
    assert w.polls == before


def test_poll_errors_are_reported_without_killing_loop():
    errors=[]
    class Broken(Worker):
        def poll_once(self):
            raise RuntimeError("poll failed")

    w=Broken()
    lifecycle=WorkerLifecycle(w, poll_interval=0.01, on_error=errors.append)
    lifecycle.start()
    time.sleep(0.03)
    lifecycle.stop(timeout=1)
    assert errors


def test_invalid_poll_interval_is_rejected():
    try:
        WorkerLifecycle(Worker(), poll_interval=0)
        assert False
    except ValueError:
        assert True
