from __future__ import annotations
import hashlib


class JobService:
    def __init__(self, store, state_machine):
        self.store = store
        self.sm = state_machine

    def create_from_github(self, payload, commit_sha):
        # Stable id makes webhook retries idempotent at the application layer.
        raw = f"{payload.repository}:{payload.delivery_id}:{commit_sha}".encode()
        job_id = hashlib.sha256(raw).hexdigest()[:32]

        from packages.jobs.state import JobRecord
        job = JobRecord(
            job_id=job_id,
            repository=payload.repository,
            delivery_id=payload.delivery_id,
            commit_sha=commit_sha,
        )
        try:
            return self.store.create(job)
        except ValueError as exc:
            if "duplicate GitHub delivery" in str(exc):
                for existing in self.store.all():
                    if existing.delivery_id == payload.delivery_id:
                        return existing
            raise

    def transition(self, job_id, target):
        job = self.store.get(job_id)
        if not job:
            raise KeyError(job_id)
        updated = self.sm.transition(job, target)
        return self.store.update(updated)

    def fail(self, job_id, error):
        job = self.store.get(job_id)
        if not job:
            raise KeyError(job_id)
        return self.store.update(self.sm.fail(job, error))
