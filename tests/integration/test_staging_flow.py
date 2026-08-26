import hashlib
import hmac
import json

from fastapi.testclient import TestClient
from packages.api.app import create_app
from packages.webhooks.handlers import WebhookDispatcher


class FakeJobs:
    def __init__(self):
        self.deliveries = set()
        self.jobs = {}

    def exists_delivery(self, delivery_id):
        return delivery_id in self.deliveries

    def create_from_webhook(self, **kwargs):
        self.deliveries.add(kwargs["delivery_id"])
        job = type("Job", (), {"job_id": f"job-{len(self.jobs)+1}"})()
        self.jobs[job.job_id] = kwargs
        return job


class Queue:
    def __init__(self):
        self.ids = []

    def __call__(self, job_id):
        self.ids.append(job_id)


def sign(secret, body):
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_staging_webhook_to_queue_flow():
    jobs = FakeJobs()
    queue = Queue()
    dispatcher = WebhookDispatcher(jobs, queue)
    app = create_app(dispatcher=dispatcher, webhook_secret="staging-secret")
    client = TestClient(app)

    payload = {
        "repository": {"full_name": "patchproof/staging-fixture"},
        "alert": {"most_recent_instance": {"commit_sha": "a" * 40}},
    }
    body = json.dumps(payload).encode()

    response = client.post(
        "/webhooks/github",
        content=body,
        headers={
            "X-Hub-Signature-256": sign("staging-secret", body),
            "X-GitHub-Event": "code_scanning_alert",
            "X-GitHub-Delivery": "staging-delivery-1",
        },
    )

    assert response.status_code == 200
    assert response.json()["accepted"] is True
    assert queue.ids == ["job-1"]
    assert jobs.jobs["job-1"]["repository"] == "patchproof/staging-fixture"


def test_staging_duplicate_delivery_does_not_enqueue_twice():
    jobs = FakeJobs()
    queue = Queue()
    app = create_app(
        dispatcher=WebhookDispatcher(jobs, queue),
        webhook_secret="staging-secret",
    )
    client = TestClient(app)

    payload = {
        "repository": {"full_name": "patchproof/staging-fixture"},
        "alert": {"most_recent_instance": {"commit_sha": "b" * 40}},
    }
    body = json.dumps(payload).encode()
    headers = {
        "X-Hub-Signature-256": sign("staging-secret", body),
        "X-GitHub-Event": "code_scanning_alert",
        "X-GitHub-Delivery": "same-delivery",
    }

    assert client.post("/webhooks/github", content=body, headers=headers).status_code == 200
    second = client.post("/webhooks/github", content=body, headers=headers)

    assert second.status_code == 200
    assert second.json()["duplicate"] is True
    assert queue.ids == ["job-1"]
