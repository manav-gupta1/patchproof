import hashlib
import hmac
import json

import pytest

from packages.github.app import GitHubAppConfig, GitHubWebhookHandler
from packages.github.worker import GitHubRemediationWorker


def signed(body, secret):
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_webhook_signature_and_finding_normalization():
    secret = "test-secret"
    body = json.dumps({
        "repository": {"full_name": "acme/demo"},
        "installation": {"id": 123},
        "alert": {
            "number": 7,
            "html_url": "https://github.com/acme/demo/security/code-scanning/7",
            "rule": {
                "id": "py/sql-injection",
                "description": "SQL injection",
                "security_severity_level": "high",
            },
            "most_recent_instance": {
                "location": {
                    "path": "app/db.py",
                    "start_line": 4,
                    "end_line": 4,
                }
            },
        },
    }).encode()

    handler = GitHubWebhookHandler(GitHubAppConfig("42", secret))
    payload = handler.parse(body, {
        "x-hub-signature-256": signed(body, secret),
        "x-github-event": "code_scanning_alert",
        "x-github-delivery": "delivery-1",
    })

    assert payload.repository == "acme/demo"
    assert payload.installation_id == 123
    assert payload.finding["rule_id"] == "py/sql-injection"
    assert payload.finding["path"] == "app/db.py"


def test_invalid_signature_fails_closed():
    handler = GitHubWebhookHandler(GitHubAppConfig("42", "secret"))
    with pytest.raises(PermissionError):
        handler.parse(b"{}", {
            "x-hub-signature-256": "sha256=bad",
            "x-github-event": "code_scanning_alert",
        })


def test_worker_enqueues_normalized_job():
    class Queue:
        def __init__(self): self.items = []
        def enqueue(self, item): self.items.append(item)

    body = json.dumps({
        "repository": {"full_name": "acme/demo"},
        "alert": {"rule": {"id": "x"}, "most_recent_instance": {}},
    }).encode()
    handler = GitHubWebhookHandler(GitHubAppConfig("42", "s"))
    sig = signed(body, "s")
    payload = handler.parse(body, {
        "x-hub-signature-256": sig,
        "x-github-event": "code_scanning_alert",
        "x-github-delivery": "d1",
    })
    q = Queue()
    job = GitHubRemediationWorker(q).enqueue(payload)
    assert q.items[0] == job
    assert job.repository == "acme/demo"
