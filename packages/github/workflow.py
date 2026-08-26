from __future__ import annotations
from dataclasses import dataclass

from packages.github.webhook import WebhookDeduplicator, WebhookEvent


@dataclass(frozen=True)
class RemediationTrigger:
    delivery_id: str
    repository: str
    finding_key: str
    ref: str


class GitHubRemediationWorkflow:
    def __init__(self, deduplicator=None):
        self.deduplicator = deduplicator or WebhookDeduplicator()

    def accept(self, event: WebhookEvent, *, finding_key: str, ref: str):
        if not self.deduplicator.claim(event.delivery_id):
            return None
        if not finding_key or not ref:
            raise ValueError("finding key and ref are required")
        return RemediationTrigger(
            delivery_id=event.delivery_id,
            repository=event.repository,
            finding_key=finding_key,
            ref=ref,
        )
