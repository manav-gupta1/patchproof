from celery import Celery

from packages.core.config import get_settings

settings = get_settings()
celery_app = Celery("patchproof", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(task_track_started=True, task_serializer="json", result_serializer="json", accept_content=["json"])
