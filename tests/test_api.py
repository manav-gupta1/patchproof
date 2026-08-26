import hashlib
import hmac
import json
from fastapi.testclient import TestClient

from packages.api.app import create_app


class Dispatcher:
    def __init__(self):
        self.events = []

    def dispatch(self, event):
        self.events.append(event)
        return {"accepted": True, "job_id": "j1"}


def signed(secret, payload):
    body = json.dumps(payload).encode()
    sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return body, sig


def test_health():
    app = create_app(dispatcher=Dispatcher(), webhook_secret="secret")
    assert TestClient(app).get("/healthz").json() == {"status": "ok"}


def test_webhook_auth_and_dispatch():
    dispatcher = Dispatcher()
    app = create_app(dispatcher=dispatcher, webhook_secret="secret")
    client = TestClient(app)
    payload = {"repository": {"full_name": "acme/staging"}}
    body, sig = signed("secret", payload)
    response = client.post(
        "/webhooks/github",
        content=body,
        headers={
            "X-Hub-Signature-256": sig,
            "X-GitHub-Event": "code_scanning_alert",
            "X-GitHub-Delivery": "d1",
        },
    )
    assert response.status_code == 200
    assert response.json()["job_id"] == "j1"


def test_bad_signature_is_401():
    app = create_app(dispatcher=Dispatcher(), webhook_secret="secret")
    response = TestClient(app).post(
        "/webhooks/github",
        content=b"{}",
        headers={
            "X-Hub-Signature-256": "sha256=bad",
            "X-GitHub-Event": "code_scanning_alert",
            "X-GitHub-Delivery": "d1",
        },
    )
    assert response.status_code == 401
