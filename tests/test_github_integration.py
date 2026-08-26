import hashlib
import hmac
import json

from packages.integrations.github import parse_code_scanning_alert, verify_signature
from packages.evidence.pr import build_pr_body


def test_signature_and_alert_parsing():
    body = b'{"action":"created"}'
    secret = "secret"
    sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_signature(secret, body, sig)
    assert not verify_signature(secret, body, "sha256=bad")

    finding = parse_code_scanning_alert({
        "repository": {"full_name": "acme/app"},
        "alert": {
            "rule": {"id": "python.sql"},
            "severity": "high",
        },
        "most_recent_instance": {
            "commit_sha": "abc",
            "fingerprint": "fp",
            "location": {
                "path": "app.py",
                "start_line": 10,
                "end_line": 10,
            },
        },
    })
    assert finding.repository == "acme/app"
    assert finding.commit_sha == "abc"
    assert finding.fingerprint == "fp"
    assert finding.start_line == 10


def test_alert_fingerprint_fallback():
    finding = parse_code_scanning_alert({
        "repository": {"full_name": "acme/app"},
        "alert": {
            "fingerprint": "alert-fp",
            "rule": {"id": "r"},
        },
    })
    assert finding.fingerprint == "alert-fp"


def test_pr_body_contains_executable_verdict():
    body = build_pr_body(
        finding={
            "rule_id": "r",
            "path": "app.py",
            "start_line": 1,
            "end_line": 1,
            "fingerprint": "fp",
        },
        patch={
            "model_provider": "test",
            "model_name": "m",
            "patch_id": "p",
        },
        verification={
            "verified": True,
            "baseline_reproduced": True,
            "patched_blocked": True,
            "tests_passed": True,
            "semgrep_clean": True,
            "semgrep_finding_count": 0,
        },
        evidence_id="evidence123",
    )
    assert "VERIFIED" in body
    assert "evidence123" in body
    assert "model output as verification" in body
