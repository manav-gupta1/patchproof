from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LeaseDecision:
    renewed: bool
    owner: str


class LeaseRaceGuard:
    """Model the timing boundary between renewal, expiry and result commit."""

    def __init__(self, owner, expires_at):
        self.owner = owner
        self.expires_at = expires_at
        self.completed = False

    def renew(self, worker_id, now, extension):
        if self.completed or worker_id != self.owner or now >= self.expires_at:
            return LeaseDecision(False, self.owner)
        self.expires_at = now + extension
        return LeaseDecision(True, self.owner)

    def can_commit(self, worker_id, now):
        return (
            not self.completed
            and worker_id == self.owner
            and now < self.expires_at
        )

    def commit(self, worker_id, now):
        if not self.can_commit(worker_id, now):
            return False
        self.completed = True
        return True
