from __future__ import annotations

import json


class RedisStreamQueue:
    def __init__(self, redis_client, stream="patchproof:jobs", group="workers"):
        self.redis = redis_client
        self.stream = stream
        self.group = group

    def ensure_group(self):
        try:
            self.redis.xgroup_create(self.stream, self.group, id="0", mkstream=True)
        except Exception as exc:
            # Redis BUSYGROUP is safe to ignore; other errors propagate.
            if "BUSYGROUP" not in str(exc):
                raise

    def enqueue(self, job_id: str):
        return self.redis.xadd(self.stream, {"job_id": job_id})

    def read(self, consumer: str, count=1, block_ms=5000):
        return self.redis.xreadgroup(
            self.group, consumer, {self.stream: ">"}, count=count, block=block_ms
        )

    def ack(self, message_id):
        return self.redis.xack(self.stream, self.group, message_id)

    def reclaim_idle(self, min_idle_ms=60000, count=10):
        return self.redis.xautoclaim(
            self.stream, self.group, "recovery", min_idle_ms, count=count
        )
