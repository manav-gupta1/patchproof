import hashlib
import hmac

from packages.github.webhook import WebhookDeduplicator, verify_signature, WebhookEvent
from packages.github.pr import GitHubPRPayloadBuilder
from packages.github.workflow import GitHubRemediationWorkflow


def test_webhook_is_idempotent():
    d = WebhookDeduplicator()
    assert d.claim("delivery-1")
    assert not d.claim("delivery-1")
    assert d.claim("delivery-2")


def test_github_signature_is_verified():
    body = b'{"action":"created"}'
    secret = "test-secret"
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_signature(body, "sha256=" + digest, secret)
    assert not verify_signature(body, "sha256=" + "0"*64, secret)
    assert not verify_signature(body, "sha1=" + digest, secret)


def test_pr_payload_contains_verification_report():
    payload = GitHubPRPayloadBuilder(
        owner="acme", repo="demo", base="main",
        head="patchproof/fix-abc123",
        title="fix: remediate SQL injection",
        body="## PatchProof: VERIFIED\n\nEvidence: manifest.json",
    ).build()
    assert payload["head"].startswith("patchproof/")
    assert "VERIFIED" in payload["body"]


def test_duplicate_github_delivery_does_not_create_second_job():
    event = WebhookEvent("delivery-1", "code_scanning_alert", "acme/demo", {})
    workflow = GitHubRemediationWorkflow()
    first = workflow.accept(event, finding_key="fp-123", ref="abc")
    second = workflow.accept(event, finding_key="fp-123", ref="abc")
    assert first is not None
    assert second is None
