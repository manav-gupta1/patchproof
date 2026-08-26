from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
import yaml

from packages.github.auth import sanitize_secret_text
from packages.policy.models import (
    GlobalPolicy,
    RepositoryPolicy,
    RulePolicy,
    Severity,
)

logger = logging.getLogger(__name__)

POLICY_FILENAMES = [".patchproof.yml", ".patchproof.yaml"]


class InvalidPolicyError(ValueError):
    """Raised when repository policy file contains invalid YAML or invalid schema."""
    pass


class PolicyLoader:
    """Loads and validates .patchproof.yml repository policies."""

    @classmethod
    def load_from_workspace(cls, workspace_path: str | Path) -> RepositoryPolicy:
        workspace = Path(workspace_path)
        for name in POLICY_FILENAMES:
            policy_file = workspace / name
            if policy_file.is_file():
                try:
                    content = policy_file.read_text(encoding="utf-8")
                    return cls.parse_yaml(content, source=name)
                except Exception as exc:
                    sanitized_err = sanitize_secret_text(str(exc))
                    logger.warning("Failed to load policy file %s: %s", name, sanitized_err)
                    return RepositoryPolicy(
                        source=name,
                        is_valid=False,
                        validation_error=f"Failed to parse {name}: {sanitized_err}",
                    )

        # No policy file found; return safe defaults
        return RepositoryPolicy(source="default", is_valid=True)

    @classmethod
    def parse_yaml(cls, content: str, source: str = ".patchproof.yml") -> RepositoryPolicy:
        """Parses YAML content safely and validates against policy schema."""
        try:
            parsed = yaml.safe_load(content)
        except Exception as exc:
            sanitized_err = sanitize_secret_text(str(exc))
            return RepositoryPolicy(
                source=source,
                is_valid=False,
                validation_error=f"Invalid YAML syntax: {sanitized_err}",
            )

        if parsed is None:
            # Empty file defaults to valid default policy
            return RepositoryPolicy(source=source, is_valid=True)

        if not isinstance(parsed, dict):
            return RepositoryPolicy(
                source=source,
                is_valid=False,
                validation_error="Top-level configuration must be a YAML mapping/dictionary",
            )

        # Schema Validation
        try:
            policy_version = str(parsed.get("version", "1.0"))
            raw_global = parsed.get("policy", {})
            if not isinstance(raw_global, dict):
                raise InvalidPolicyError("'policy' section must be a mapping/dictionary")

            # Validate global fields
            enabled = raw_global.get("enabled", True)
            if not isinstance(enabled, bool):
                raise InvalidPolicyError("'policy.enabled' must be a boolean")

            raw_min_sev = raw_global.get("minimum_severity", "medium")
            try:
                min_sev = Severity.from_str(str(raw_min_sev))
            except ValueError as e:
                raise InvalidPolicyError(f"Invalid 'policy.minimum_severity': {e}") from e

            auto_remediate = raw_global.get("auto_remediate", True)
            if not isinstance(auto_remediate, bool):
                raise InvalidPolicyError("'policy.auto_remediate' must be a boolean")

            auto_create_pr = raw_global.get("auto_create_pr", True)
            if not isinstance(auto_create_pr, bool):
                raise InvalidPolicyError("'policy.auto_create_pr' must be a boolean")

            target_branches = raw_global.get("target_branches", ["main", "master"])
            if not isinstance(target_branches, list) or not all(isinstance(b, str) for b in target_branches):
                raise InvalidPolicyError("'policy.target_branches' must be a list of strings")

            allowed_events = raw_global.get(
                "allowed_events", ["pull_request", "code_scanning_alert", "check_run"]
            )
            if not isinstance(allowed_events, list) or not all(isinstance(e, str) for e in allowed_events):
                raise InvalidPolicyError("'policy.allowed_events' must be a list of strings")

            global_policy = GlobalPolicy(
                enabled=enabled,
                minimum_severity=min_sev,
                auto_remediate=auto_remediate,
                auto_create_pr=auto_create_pr,
                target_branches=target_branches,
                allowed_events=allowed_events,
            )

            # Validate rules section
            rules_dict: dict[str, RulePolicy] = {}
            raw_rules = parsed.get("rules", {})
            if raw_rules is not None:
                if not isinstance(raw_rules, dict):
                    raise InvalidPolicyError("'rules' section must be a mapping of rule IDs to rule configurations")

                for rule_id, rule_conf in raw_rules.items():
                    if not isinstance(rule_conf, dict):
                        raise InvalidPolicyError(f"Configuration for rule '{rule_id}' must be a mapping")

                    rule_enabled = rule_conf.get("enabled", True)
                    if not isinstance(rule_enabled, bool):
                        raise InvalidPolicyError(f"'enabled' for rule '{rule_id}' must be a boolean")

                    rule_auto_rem = rule_conf.get("auto_remediate")
                    if rule_auto_rem is not None and not isinstance(rule_auto_rem, bool):
                        raise InvalidPolicyError(f"'auto_remediate' for rule '{rule_id}' must be a boolean")

                    rules_dict[str(rule_id)] = RulePolicy(
                        enabled=rule_enabled,
                        auto_remediate=rule_auto_rem,
                    )

            return RepositoryPolicy(
                version=policy_version,
                policy=global_policy,
                rules=rules_dict,
                source=source,
                is_valid=True,
            )

        except InvalidPolicyError as err:
            clean_msg = sanitize_secret_text(str(err))
            return RepositoryPolicy(
                source=source,
                is_valid=False,
                validation_error=clean_msg,
            )
        except Exception as exc:
            clean_msg = sanitize_secret_text(str(exc))
            return RepositoryPolicy(
                source=source,
                is_valid=False,
                validation_error=f"Schema validation error: {clean_msg}",
            )
