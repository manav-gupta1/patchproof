from apps.worker.celery_app import celery_app


@celery_app.task(name="patchproof.health_check")
def health_check() -> dict[str, str]:
    return {"status": "ok", "worker": "celery"}
