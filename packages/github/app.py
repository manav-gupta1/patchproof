from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib
import hmac
import json


@dataclass(frozen=True)
class GitHubAppConfig:
    app_id: str
    webhook_secret: str
    private_key: str | None = None

    def __post_init__(self):
        if not self.app_id:
            raise ValueError("app_id is required")
        if not self.webhook_secret:
            raise ValueError("webhook_secret is required")


@dataclass(frozen=True)
class GitHubCheckPayload:
    repository: str
    installation_id: int | None
    event: str
    delivery_id: str
    finding: dict

    def as_dict(self):
        return asdict(self)


class GitHubWebhookHandler:
    """Validate GitHub webhook signatures and normalize supported events."""

    SUPPORTED_EVENTS = {"code_scanning_alert", "check_run", "pull_request"}

    def __init__(self, config: GitHubAppConfig):
        self.config = config

    def verify_signature(self, body: bytes, signature: str) -> bool:
        prefix = "sha256="
        if not signature.startswith(prefix):
            return False
        supplied = signature[len(prefix):]
        expected = hmac.new(
            self.config.webhook_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, supplied)

    def parse(self, body: bytes, headers: dict[str, str]) -> GitHubCheckPayload | None:
        signature = headers.get("x-hub-signature-256", "")
        if not self.verify_signature(body, signature):
            raise PermissionError("invalid GitHub webhook signature")

        event = headers.get("x-github-event", "")
        if event not in self.SUPPORTED_EVENTS:
            return None

        delivery = headers.get("x-github-delivery", "")
        payload = json.loads(body.decode("utf-8"))
        repo = payload.get("repository", {}).get("full_name")
        if not repo:
            raise ValueError("webhook missing repository.full_name")

        installation = payload.get("installation") or {}
        finding = self._finding_from_payload(event, payload)

        return GitHubCheckPayload(
            repository=repo,
            installation_id=installation.get("id"),
            event=event,
            delivery_id=delivery,
            finding=finding,
        )

    @staticmethod
    def _finding_from_payload(event, payload):
        if event == "code_scanning_alert":
            alert = payload.get("alert") or {}
            rule = alert.get("rule") or {}
            instance = alert.get("most_recent_instance") or {}
            location = instance.get("location") or {}
            return {
                "alert_number": alert.get("number"),
                "rule_id": rule.get("id"),
                "message": rule.get("description"),
                "severity": rule.get("security_severity_level") or rule.get("severity"),
                "path": location.get("path"),
                "start_line": location.get("start_line"),
                "end_line": location.get("end_line"),
                "html_url": alert.get("html_url"),
            }

        if event == "pull_request":
            pr = payload.get("pull_request") or {}
            head = pr.get("head") or {}
            return {
                "alert_number": pr.get("number"),
                "pr_number": pr.get("number"),
                "head_sha": head.get("sha") or pr.get("head_sha") or f"pr-{pr.get('number')}",
                "action": payload.get("action"),
            }

        check = payload.get("check_run") or {}
        return {
            "check_run_id": check.get("id"),
            "name": check.get("name"),
            "status": check.get("status"),
            "conclusion": check.get("conclusion"),
            "head_sha": check.get("head_sha"),
        }
