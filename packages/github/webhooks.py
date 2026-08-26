from __future__ import annotations

import hashlib
import hmac
import json

from packages.github.models import WebhookEvent


class WebhookVerificationError(ValueError):
    pass


class GitHubWebhookParser:
    def __init__(self, secret: bytes) -> None:
        self.secret = secret

    def verify_signature(self, body: bytes, signature: str) -> bool:
        expected = "sha256=" + hmac.new(
            self.secret, body, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def parse(
        self,
        *,
        body: bytes,
        signature: str,
        event: str,
        delivery_id: str,
    ) -> WebhookEvent:
        if not self.verify_signature(body, signature):
            raise WebhookVerificationError("invalid webhook signature")

        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise WebhookVerificationError("invalid JSON payload") from exc

        return WebhookEvent(
            event=event,
            delivery_id=delivery_id,
            payload=payload,
        )
