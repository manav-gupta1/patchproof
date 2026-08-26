from __future__ import annotations

import logging
import time

from packages.state import JobState

logger = logging.getLogger(__name__)


class JobWorker:
    def __init__(self, queue, repository, pipeline):
        self.queue = queue
        self.repository = repository
        self.pipeline = pipeline

    def process_once(self):
        message = self.queue.claim(timeout=1)
        if message is None:
            return False

        job_id = message["job_id"]
        job = self.repository.get_job(job_id)
        if job is None:
            logger.error("job %s disappeared before processing", job_id)
            return True

        try:
            self.pipeline.run(job, self.repository)
        except Exception:
            logger.exception("job %s failed", job_id)
            # A real implementation should attach the exception as evidence
            # before moving the job to REJECTED.
            if job.state not in {JobState.REJECTED, JobState.MERGED}:
                try:
                    self.repository.transition(
                        job,
                        to_state=JobState.REJECTED,
                        actor="worker",
                        reason="pipeline exception",
                    )
                except Exception:
                    logger.exception("failed to reject job %s", job_id)
        return True

    def run_forever(self, sleep_seconds: float = 0.25):
        while True:
            processed = self.process_once()
            if not processed:
                time.sleep(sleep_seconds)
