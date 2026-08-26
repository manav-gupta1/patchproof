import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from apps.api.main import app, jobs, queue


def test_health():
    assert TestClient(app).get("/health").json() == {"status": "ok"}


def test_github_webhook_creates_job_and_queue_task():
    secret = b"development-secret"
    payload = {
        "repository": {"full_name": "acme/app"},
        "commit_sha": "abc",
        "alert": {
            "number": 1,
            "rule": {"id": "python.sql-injection", "security_severity_level": "high"},
            "most_recent_instance": {
                "fingerprint": "fp",
                "location": {"path": "app.py", "start_line": 4, "end_line": 4},
            },
        },
    }
    body = json.dumps(payload).encode()
    signature = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()

    response = TestClient(app).post(
        "/webhooks/github",
        content=body,
        headers={
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "code_scanning_alert",
            "X-GitHub-Delivery": "delivery-1",
        },
    )

    assert response.status_code == 200
    job_id = response.json()["jobs"][0]
    assert jobs.get(job_id).state.value == "received"
    task = queue.dequeue()
    assert task is not None
    assert task.job_id == job_id
    assert task.path == "app.py"


def test_invalid_webhook_is_rejected():
    response = TestClient(app).post(
        "/webhooks/github",
        content=b"{}",
        headers={
            "X-Hub-Signature-256": "sha256=bad",
            "X-GitHub-Event": "code_scanning_alert",
            "X-GitHub-Delivery": "delivery-2",
        },
    )
    assert response.status_code == 401
