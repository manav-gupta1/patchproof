from __future__ import annotations

_orchestrator = None


def configure_orchestrator(orchestrator):
    global _orchestrator
    _orchestrator = orchestrator


def get_orchestrator():
    if _orchestrator is None:
        raise RuntimeError("remediation orchestrator has not been configured")
    return _orchestrator
