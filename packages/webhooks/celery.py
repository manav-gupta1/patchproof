from __future__ import annotations


def build_enqueue(celery_task):
    def enqueue(job_id):
        celery_task.delay(job_id)
    return enqueue
