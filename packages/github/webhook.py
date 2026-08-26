from __future__ import annotations
from dataclasses import dataclass
import hashlib
import hmac
import json


@dataclass(frozen=True)
class WebhookEvent:
    delivery_id: str
    event_name: str
    repository: str
    payload: dict


class WebhookDeduplicator:
    """Idempotency boundary for GitHub webhook deliveries."""
    def __init__(self):
        self._seen: set[str] = set()

    def claim(self, delivery_id: str) -> bool:
        if not delivery_id:
            raise ValueError("missing GitHub delivery id")
        if delivery_id in self._seen:
            return False
        self._seen.add(delivery_id)
        return True


def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    if not signature.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature[7:], expected)
