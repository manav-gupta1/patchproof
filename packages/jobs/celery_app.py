from __future__ import annotations
import os

redis_url = os.environ.get("PATCHPROOF_REDIS_URL", "redis://localhost:6379/0")

try:
    from celery import Celery
    from celery.signals import worker_process_init, worker_init
except ImportError:
    Celery = None
    worker_init = None
    worker_process_init = None


def _setup_default_worker_orchestrator():
    from packages.jobs.pipeline_factory import create_concrete_remediation_orchestrator
    from packages.store.postgres import PostgresJobStore
    from packages.jobs.runtime import configure_orchestrator

    db_url = os.environ.get("PATCHPROOF_DATABASE_URL")
    if db_url:
        store = PostgresJobStore(db_url)
    else:
        from packages.jobs.store import InMemoryJobStore
        store = InMemoryJobStore()

    github_client = None
    try:
        from packages.github.auth import GitHubAppCredentials, GitHubAppAuth
        from packages.github.client import GitHubAppClient
        creds = GitHubAppCredentials.from_env()
        if creds.app_id and creds.private_key_pem:
            auth = GitHubAppAuth(
                app_id=creds.app_id,
                private_key_pem=creds.private_key_pem,
                api_url=creds.api_url,
            )
            github_client = GitHubAppClient(auth=auth)
    except Exception:
        github_client = None

    orchestrator = create_concrete_remediation_orchestrator(store=store, github_client=github_client)
    configure_orchestrator(orchestrator)


if Celery is not None:
    celery_app = Celery("patchproof", broker=redis_url, backend=redis_url)
    celery_app.conf.update(
        task_acks_late=True, worker_prefetch_multiplier=1,
        task_reject_on_worker_lost=True, task_time_limit=900,
        task_soft_time_limit=840,
    )
    if worker_process_init is not None:
        @worker_process_init.connect
        def _on_worker_process_init(**kwargs):
            import packages.jobs.runtime as runtime
            if runtime._orchestrator is None:
                _setup_default_worker_orchestrator()

    if worker_init is not None:
        @worker_init.connect
        def _on_worker_init(**kwargs):
            import packages.jobs.runtime as runtime
            if runtime._orchestrator is None:
                _setup_default_worker_orchestrator()
else:
    class _Task:
        def __init__(self, fn): self.fn = fn
        def __call__(self, *a, **kw): return self.fn(*a, **kw)
    class _CeleryFallback:
        def __init__(self): self.tasks = {}
        def task(self, *args, **kwargs):
            def deco(fn):
                task = _Task(fn)
                self.tasks[f"packages.jobs.celery_app.{fn.__name__}"] = task
                return task
            return deco
    celery_app = _CeleryFallback()

@celery_app.task(
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def remediation_task(self, job_id: str):
    import packages.jobs.runtime as runtime
    if runtime._orchestrator is None:
        _setup_default_worker_orchestrator()
    from packages.jobs.runtime import get_orchestrator
    return get_orchestrator().run(job_id)
