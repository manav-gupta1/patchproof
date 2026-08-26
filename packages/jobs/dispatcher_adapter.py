from __future__ import annotations


class CeleryDispatcher:
    def __init__(self, jobs, celery_task):
        self.jobs = jobs
        self.celery_task = celery_task

    def exists_delivery(self, delivery_id):
        return self.jobs.exists_delivery(delivery_id)

    def create_from_webhook(self, **kwargs):
        return self.jobs.create_from_webhook(**kwargs)

    def enqueue(self, job_id):
        return self.celery_task.delay(job_id)
