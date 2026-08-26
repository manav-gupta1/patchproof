import hashlib
import hmac
import json
from fastapi.testclient import TestClient

from packages.api.app import create_app
from packages.webhooks.handlers import WebhookDispatcher


class FakeJobStore:
    def __init__(self):
        self.deliveries = set()
        self.jobs = {}

    def exists_delivery(self, delivery_id: str) -> bool:
        return delivery_id in self.deliveries

    def create_from_webhook(self, **kwargs):
        self.deliveries.add(kwargs["delivery_id"])
        job = type("Job", (), {"job_id": f"job-{kwargs['delivery_id']}"})()
        self.jobs[job.job_id] = kwargs
        return job


class FakeQueue:
    def __init__(self):
        self.enqueued = []

    def __call__(self, job_id: str):
        self.enqueued.append(job_id)


def sign(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_pull_request_webhook_dispatches_and_enqueues():
    store = FakeJobStore()
    queue = FakeQueue()
    dispatcher = WebhookDispatcher(store, queue)
    app = create_app(dispatcher=dispatcher, webhook_secret="test-secret")
    client = TestClient(app)

    payload = {
        "action": "opened",
        "repository": {"full_name": "example/patchproof-fixture"},
        "pull_request": {
            "number": 1,
            "head": {"sha": "c0ffee1234567890abcdef1234567890abcdef12"},
        },
    }
    body = json.dumps(payload).encode()
    signature = sign("test-secret", body)

    response = client.post(
        "/webhooks/github",
        content=body,
        headers={
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "test-pr-delivery-001",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["accepted"] is True
    assert data["job_id"] == "job-test-pr-delivery-001"
    assert queue.enqueued == ["job-test-pr-delivery-001"]
    assert store.jobs["job-test-pr-delivery-001"]["repository"] == "example/patchproof-fixture"
    assert store.jobs["job-test-pr-delivery-001"]["commit_sha"] == "c0ffee1234567890abcdef1234567890abcdef12"


def test_pull_request_webhook_fixture_payload_without_head_sha():
    store = FakeJobStore()
    queue = FakeQueue()
    dispatcher = WebhookDispatcher(store, queue)
    app = create_app(dispatcher=dispatcher, webhook_secret="test-secret")
    client = TestClient(app)

    # Payload matching /tmp/github-payload.json
    payload = {
        "action": "opened",
        "repository": {"full_name": "example/patchproof-fixture"},
        "pull_request": {"number": 1},
    }
    body = json.dumps(payload).encode()
    signature = sign("test-secret", body)

    response = client.post(
        "/webhooks/github",
        content=body,
        headers={
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "test-delivery-fixture-001",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["accepted"] is True
    assert data["job_id"] == "job-test-delivery-fixture-001"
    assert queue.enqueued == ["job-test-delivery-fixture-001"]
