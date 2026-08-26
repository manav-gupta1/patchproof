from __future__ import annotations

import json


class ProbeHTTP:
    """Small framework-neutral HTTP contract for health/readiness probes."""

    def __init__(self, probe_service):
        self.probe_service = probe_service

    def health(self):
        status = self.probe_service.health()
        return self._response(status.healthy, {"checks": status.checks})

    def readiness(self):
        status = self.probe_service.readiness()
        return self._response(
            status.ready,
            {"reason": status.reason},
        )

    @staticmethod
    def _response(ok, body):
        return {
            "status": 200 if ok else 503,
            "content_type": "application/json",
            "body": json.dumps(body, sort_keys=True),
        }
