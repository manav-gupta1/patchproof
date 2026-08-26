from __future__ import annotations
import os

from packages.jobs.celery_app import celery_app

if celery_app is not None:
    @celery_app.task(
        bind=True,
        autoretry_for=(RuntimeError,),
        retry_backoff=True,
        retry_jitter=True,
        max_retries=3,
    )
    def run_remediation(self, job_id: str):
        # The task intentionally delegates to the application service.
        # Repository execution must occur inside SandboxRunner.
        from packages.jobs.runtime import execute_job
        return execute_job(job_id)
else:
    def run_remediation(job_id: str):
        raise RuntimeError("Celery unavailable; install production dependencies")
