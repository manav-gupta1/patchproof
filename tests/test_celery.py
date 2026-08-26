import os
os.environ["PATCHPROOF_REDIS_URL"] = "redis://localhost:6379/0"

from packages.jobs.celery_app import celery_app
from packages.jobs.runtime import configure_orchestrator, get_orchestrator


def test_task_is_registered():
    assert "packages.jobs.celery_app.remediation_task" in celery_app.tasks


def test_runtime_requires_configuration():
    import packages.jobs.runtime as runtime
    runtime._orchestrator = None
    try:
        get_orchestrator()
        assert False
    except RuntimeError:
        pass

    marker = object()
    configure_orchestrator(marker)
    assert get_orchestrator() is marker
