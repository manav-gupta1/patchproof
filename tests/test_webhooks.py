import hashlib
import hmac
import json
import pytest

from packages.webhooks.github import verify_signature, parse_event, InvalidWebhook
from packages.webhooks.handlers import WebhookDispatcher


def signed(secret, payload):
    body = json.dumps(payload).encode()
    sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return body, sig


def test_github_signature():
    body, sig = signed("secret", {"ok": True})
    assert verify_signature("secret", body, sig)
    assert not verify_signature("wrong", body, sig)


def test_parse_rejects_bad_signature():
    with pytest.raises(InvalidWebhook):
        parse_event("secret", b"{}", "sha256=bad", "code_scanning_alert", "d1")


class Jobs:
    def __init__(self):
        self.deliveries = set()
        self.created = []

    def exists_delivery(self, delivery_id):
        return delivery_id in self.deliveries

    def create_from_webhook(self, **kwargs):
        self.deliveries.add(kwargs["delivery_id"])
        job = type("Job", (), {"job_id": "j1"})()
        self.created.append(kwargs)
        return job


def test_dispatch_is_idempotent():
    jobs = Jobs()
    queued = []
    dispatcher = WebhookDispatcher(jobs, queued.append)
    event = parse_event(
        "secret",
        *signed("secret", {
            "repository": {"full_name": "acme/staging"},
            "alert": {"most_recent_instance": {"commit_sha": "a"*40}},
        }),
        event="code_scanning_alert",
        delivery_id="delivery-1",
    )
    assert dispatcher.dispatch(event)["accepted"]
    assert dispatcher.dispatch(event)["duplicate"]
    assert queued == ["j1"]
    assert len(jobs.created) == 1
