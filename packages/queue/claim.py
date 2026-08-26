from __future__ import annotations

import json
import time
import uuid


class DurableJobQueue:
    """
    Redis Streams based queue contract.

    This is the production queue boundary. Unlike a plain list, Streams give
    us consumer groups and pending-entry tracking so a crashed worker can be
    reclaimed.
    """

    STREAM = "patchproof:jobs"
    GROUP = "patchproof-workers"

    def __init__(self, client):
        self.client = client
        try:
            self.client.xgroup_create(self.STREAM, self.GROUP, id="0", mkstream=True)
        except Exception as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    def enqueue(self, job_id: str) -> str:
        return self.client.xadd(
            self.STREAM,
            {"job_id": job_id, "message_id": str(uuid.uuid4())},
        )

    def claim(self, consumer: str, count: int = 1, block_ms: int = 1000):
        entries = self.client.xreadgroup(
            self.GROUP,
            consumer,
            {self.STREAM: ">"},
            count=count,
            block=block_ms,
        )
        if not entries:
            return []
        return entries[0][1]

    def ack(self, entry_id: str) -> int:
        return self.client.xack(self.STREAM, self.GROUP, entry_id)

    def reclaim(self, consumer: str, min_idle_ms: int = 60_000, count: int = 10):
        result = self.client.xautoclaim(
            self.STREAM,
            self.GROUP,
            consumer,
            min_idle_time=min_idle_ms,
            start_id="0-0",
            count=count,
        )
        return result[1]
