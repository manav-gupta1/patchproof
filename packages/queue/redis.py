from __future__ import annotations

import json

from packages.queue.models import RemediationTask


class RedisQueue:
    """Redis-backed queue contract.

    Production deployment should use Redis ACLs/TLS and a dedicated queue key.
    """

    def __init__(self, client, key: str = "patchproof:remediation") -> None:
        self.client = client
        self.key = key

    def enqueue(self, task: RemediationTask) -> str:
        self.client.rpush(self.key, task.model_dump_json())
        return task.job_id

    def dequeue(self) -> RemediationTask | None:
        raw = self.client.lpop(self.key)
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return RemediationTask.model_validate(json.loads(raw))
