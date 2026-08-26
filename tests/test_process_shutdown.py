import signal
from packages.jobs.process_shutdown import ProcessShutdown

class Lifecycle:
    def __init__(self):
        self.calls=[]
    def stop(self, timeout=30):
        self.calls.append(timeout)

def test_shutdown_is_idempotent():
    l=Lifecycle()
    s=ProcessShutdown(l, stop_timeout=7)
    s.shutdown()
    s.shutdown()
    assert l.calls == [7]

def test_install_and_uninstall_restore_handlers():
    l=Lifecycle()
    s=ProcessShutdown(l)
    old_term=signal.getsignal(signal.SIGTERM)
    old_int=signal.getsignal(signal.SIGINT)
    s.install()
    assert signal.getsignal(signal.SIGTERM) == s._handle
    assert signal.getsignal(signal.SIGINT) == s._handle
    s.uninstall()
    assert signal.getsignal(signal.SIGTERM) == old_term
    assert signal.getsignal(signal.SIGINT) == old_int

def test_signal_handler_triggers_graceful_stop():
    l=Lifecycle()
    s=ProcessShutdown(l, stop_timeout=11)
    s._handle(signal.SIGTERM, None)
    assert l.calls == [11]
