from __future__ import annotations
import hashlib
import hmac
import json
from dataclasses import dataclass


class InvalidWebhook(ValueError):
    pass


def verify_signature(secret: str, body: bytes, signature: str) -> bool:
    if not signature or not signature.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        secret.encode(), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@dataclass(frozen=True)
class GitHubEvent:
    delivery_id: str
    event: str
    payload: dict


MAX_WEBHOOK_BODY_BYTES = 5 * 1024 * 1024  # 5MB maximum webhook payload limit


def parse_event(secret: str, body: bytes, signature: str, event: str, delivery_id: str):
    if len(body) > MAX_WEBHOOK_BODY_BYTES:
        raise InvalidWebhook("payload exceeds maximum allowed size (5MB)")
    if not verify_signature(secret, body, signature):
        raise InvalidWebhook("invalid GitHub webhook signature")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise InvalidWebhook("invalid JSON payload") from exc
    if not delivery_id:
        raise InvalidWebhook("missing delivery ID")
    return GitHubEvent(delivery_id, event, payload)
