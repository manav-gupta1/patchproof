from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    @classmethod
    def from_str(cls, val: str) -> "Severity":
        if not isinstance(val, str):
            raise ValueError(f"Severity must be a string, got {type(val).__name__}")
        val_lower = val.strip().lower()
        for member in cls:
            if member.value == val_lower:
                return member
        raise ValueError(
            f"Invalid severity level '{val}'. Allowed levels: critical, high, medium, low, info"
        )

    @property
    def rank(self) -> int:
        ranks = {
            Severity.CRITICAL: 5,
            Severity.HIGH: 4,
            Severity.MEDIUM: 3,
            Severity.LOW: 2,
            Severity.INFO: 1,
        }
        return ranks[self]

    def __ge__(self, other: Any) -> bool:
        if isinstance(other, Severity):
            return self.rank >= other.rank
        if isinstance(other, str):
            return self.rank >= Severity.from_str(other).rank
        return NotImplemented

    def __gt__(self, other: Any) -> bool:
        if isinstance(other, Severity):
            return self.rank > other.rank
        if isinstance(other, str):
            return self.rank > Severity.from_str(other).rank
        return NotImplemented

    def __le__(self, other: Any) -> bool:
        if isinstance(other, Severity):
            return self.rank <= other.rank
        if isinstance(other, str):
            return self.rank <= Severity.from_str(other).rank
        return NotImplemented

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, Severity):
            return self.rank < other.rank
        if isinstance(other, str):
            return self.rank < Severity.from_str(other).rank
        return NotImplemented


@dataclass
class RulePolicy:
    enabled: bool = True
    auto_remediate: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"enabled": self.enabled}
        if self.auto_remediate is not None:
            d["auto_remediate"] = self.auto_remediate
        return d


@dataclass
class GlobalPolicy:
    enabled: bool = True
    minimum_severity: Severity = Severity.MEDIUM
    auto_remediate: bool = True
    auto_create_pr: bool = True
    target_branches: list[str] = field(default_factory=lambda: ["main", "master"])
    allowed_events: list[str] = field(
        default_factory=lambda: ["pull_request", "code_scanning_alert", "check_run"]
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "minimum_severity": self.minimum_severity.value,
            "auto_remediate": self.auto_remediate,
            "auto_create_pr": self.auto_create_pr,
            "target_branches": list(self.target_branches),
            "allowed_events": list(self.allowed_events),
        }


@dataclass
class RepositoryPolicy:
    version: str = "1.0"
    policy: GlobalPolicy = field(default_factory=GlobalPolicy)
    rules: dict[str, RulePolicy] = field(default_factory=dict)
    source: str = "default"  # ".patchproof.yml" or "default"
    is_valid: bool = True
    validation_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "source": self.source,
            "is_valid": self.is_valid,
            "validation_error": self.validation_error,
            "policy": self.policy.to_dict(),
            "rules": {k: v.to_dict() for k, v in self.rules.items()},
        }


@dataclass
class PolicyDecision:
    allowed: bool
    action: str  # "remediate_and_publish" | "remediate_only" | "skip_policy_disabled" | "skip_severity_too_low" | "skip_rule_disabled" | "skip_branch_not_targeted" | "skip_event_not_allowed" | "skip_auto_remediate_disabled" | "blocked_invalid_policy"
    reason: str
    rule_id: str | None = None
    severity: str | None = None
    auto_remediate: bool = True
    auto_create_pr: bool = True
    policy_source: str = "default"
    policy_version: str = "1.0"
    target_branch: str | None = None
    event_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "action": self.action,
            "reason": self.reason,
            "rule_id": self.rule_id,
            "severity": self.severity,
            "auto_remediate": self.auto_remediate,
            "auto_create_pr": self.auto_create_pr,
            "policy_source": self.policy_source,
            "policy_version": self.policy_version,
            "target_branch": self.target_branch,
            "event_type": self.event_type,
        }
