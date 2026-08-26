from __future__ import annotations

import fnmatch
from typing import Any

from packages.policy.models import (
    PolicyDecision,
    RepositoryPolicy,
    Severity,
)


class PolicyEvaluator:
    """Evaluates webhook events and scan findings against repository security policy."""

    @classmethod
    def evaluate_event(
        cls,
        policy: RepositoryPolicy,
        event_type: str | None = None,
        branch: str | None = None,
    ) -> PolicyDecision:
        """Evaluates policy gates that can be resolved before scanning (validity, enabled, event, branch)."""
        if not policy.is_valid:
            return PolicyDecision(
                allowed=False,
                action="blocked_invalid_policy",
                reason=policy.validation_error or "Invalid repository policy",
                policy_source=policy.source,
                target_branch=branch,
                event_type=event_type,
            )

        if not policy.policy.enabled:
            return PolicyDecision(
                allowed=False,
                action="skip_policy_disabled",
                reason="PatchProof security remediation is disabled by repository policy",
                policy_source=policy.source,
                target_branch=branch,
                event_type=event_type,
            )

        if event_type and policy.policy.allowed_events:
            if event_type not in policy.policy.allowed_events:
                return PolicyDecision(
                    allowed=False,
                    action="skip_event_not_allowed",
                    reason=f"Event '{event_type}' is not permitted by policy (allowed: {', '.join(policy.policy.allowed_events)})",
                    policy_source=policy.source,
                    target_branch=branch,
                    event_type=event_type,
                )

        if branch and policy.policy.target_branches:
            clean_branch = branch.replace("refs/heads/", "").strip()
            matched = any(
                clean_branch == tb or fnmatch.fnmatch(clean_branch, tb)
                for tb in policy.policy.target_branches
            )
            if not matched:
                return PolicyDecision(
                    allowed=False,
                    action="skip_branch_not_targeted",
                    reason=f"Branch '{clean_branch}' is not in configured target_branches ({', '.join(policy.policy.target_branches)})",
                    policy_source=policy.source,
                    target_branch=clean_branch,
                    event_type=event_type,
                )

        return PolicyDecision(
            allowed=True,
            action="allowed_event",
            reason="Webhook event and target branch permitted by policy",
            auto_remediate=policy.policy.auto_remediate,
            auto_create_pr=policy.policy.auto_create_pr,
            policy_source=policy.source,
            target_branch=branch,
            event_type=event_type,
        )

    @classmethod
    def evaluate_finding(
        cls,
        policy: RepositoryPolicy,
        finding: Any,
        event_type: str | None = None,
        branch: str | None = None,
    ) -> PolicyDecision:
        """Evaluates policy gates for a specific vulnerability finding."""
        # 1. First check global event and branch gates
        event_decision = cls.evaluate_event(policy, event_type=event_type, branch=branch)
        if not event_decision.allowed:
            return event_decision

        # 2. Extract finding details
        if hasattr(finding, "rule_id"):
            rule_id = str(finding.rule_id)
            severity_str = str(getattr(finding, "severity", "medium"))
        elif isinstance(finding, dict):
            rule_id = str(finding.get("rule_id", "security-issue"))
            severity_str = str(finding.get("severity", "medium"))
        else:
            rule_id = "security-issue"
            severity_str = "medium"

        try:
            sev = Severity.from_str(severity_str)
        except ValueError:
            sev = Severity.MEDIUM

        # 3. Check severity threshold
        if sev < policy.policy.minimum_severity:
            return PolicyDecision(
                allowed=False,
                action="skip_severity_too_low",
                reason=f"Finding severity '{sev.value}' is below configured minimum '{policy.policy.minimum_severity.value}'",
                rule_id=rule_id,
                severity=sev.value,
                policy_source=policy.source,
                target_branch=branch,
                event_type=event_type,
                auto_remediate=policy.policy.auto_remediate,
                auto_create_pr=policy.policy.auto_create_pr,
            )

        # 4. Check per-rule configuration
        auto_remediate = policy.policy.auto_remediate
        if rule_id in policy.rules:
            rule_policy = policy.rules[rule_id]
            if not rule_policy.enabled:
                return PolicyDecision(
                    allowed=False,
                    action="skip_rule_disabled",
                    reason=f"Remediation rule '{rule_id}' is explicitly disabled by repository policy",
                    rule_id=rule_id,
                    severity=sev.value,
                    policy_source=policy.source,
                    target_branch=branch,
                    event_type=event_type,
                    auto_remediate=False,
                    auto_create_pr=policy.policy.auto_create_pr,
                )
            if rule_policy.auto_remediate is not None:
                auto_remediate = rule_policy.auto_remediate

        # 5. Check auto-remediate permission
        if not auto_remediate:
            return PolicyDecision(
                allowed=False,
                action="skip_auto_remediate_disabled",
                reason=f"Automatic remediation is disabled for rule '{rule_id}' by policy",
                rule_id=rule_id,
                severity=sev.value,
                policy_source=policy.source,
                target_branch=branch,
                event_type=event_type,
                auto_remediate=False,
                auto_create_pr=policy.policy.auto_create_pr,
            )

        # 6. Approved for remediation
        auto_create_pr = policy.policy.auto_create_pr
        action = "remediate_and_publish" if auto_create_pr else "remediate_only"

        return PolicyDecision(
            allowed=True,
            action=action,
            reason=f"Security remediation approved for finding '{rule_id}' ({sev.value})",
            rule_id=rule_id,
            severity=sev.value,
            auto_remediate=True,
            auto_create_pr=auto_create_pr,
            policy_source=policy.source,
            target_branch=branch,
            event_type=event_type,
        )
