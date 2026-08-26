from __future__ import annotations

from packages.github.models import FindingRecord, WebhookEvent


class FindingNormalizer:
    def from_code_scanning_event(self, event: WebhookEvent) -> list[FindingRecord]:
        if event.event != "code_scanning_alert":
            return []

        payload = event.payload
        repo = payload.get("repository", {}).get("full_name", "")
        alert = payload.get("alert", {})
        rule = alert.get("rule", {})
        instance = alert.get("most_recent_instance", {})

        fingerprint = (
            instance.get("fingerprint")
            or alert.get("fingerprint")
            or str(alert.get("number", ""))
        )
        location = instance.get("location", {})
        start = location.get("start_line", 1)
        end = location.get("end_line", start)

        return [
            FindingRecord(
                fingerprint=fingerprint,
                rule_id=rule.get("id", ""),
                path=location.get("path", ""),
                start_line=start,
                end_line=end,
                severity=rule.get("security_severity_level", "unknown"),
                repository=repo,
                commit_sha=payload.get("commit_sha", ""),
            )
        ]
