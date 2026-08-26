from __future__ import annotations

import json
import os
import uuid

try:
    import redis
except ImportError:
    redis = None


class JobQueue:
    def __init__(self, url: str | None = None):
        self.url = url or os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        if redis is None:
            raise RuntimeError("redis package is required")
        self.client = redis.Redis.from_url(self.url, decode_responses=True)

    def enqueue(self, job_id: str) -> str:
        message_id = str(uuid.uuid4())
        payload = json.dumps({"message_id": message_id, "job_id": job_id})
        self.client.lpush("patchproof:jobs", payload)
        return message_id

    def claim(self, timeout: int = 5):
        item = self.client.brpop("patchproof:jobs", timeout=timeout)
        if item is None:
            return None
        _, payload = item
        return json.loads(payload)
