from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any
import pytest

from packages.github.check_runs import CheckRunRef, GitHubCheckRunReporter
from packages.github.client import GitHubAppClient
from packages.jobs.orchestrator import RemediationOrchestrator
from packages.jobs.pipeline_factory import create_concrete_remediation_orchestrator
from packages.jobs.state import JobRecord, JobState
from packages.jobs.store import InMemoryJobStore
from packages.policy.evaluator import PolicyEvaluator
from packages.policy.loader import InvalidPolicyError, PolicyLoader
from packages.policy.models import (
    GlobalPolicy,
    PolicyDecision,
    RepositoryPolicy,
    RulePolicy,
    Severity,
)
from packages.store.postgres import PostgresJobStore
from packages.webhooks.handlers import WebhookDispatcher


# ==============================================================================
# 1. Severity Ordering Tests
# ==============================================================================

def test_severity_ordering_and_comparison():
    assert Severity.CRITICAL > Severity.HIGH
    assert Severity.HIGH > Severity.MEDIUM
    assert Severity.MEDIUM > Severity.LOW
    assert Severity.LOW > Severity.INFO

    assert Severity.CRITICAL >= Severity.CRITICAL
    assert Severity.MEDIUM <= Severity.HIGH
    assert Severity.INFO < Severity.CRITICAL

    # Comparison with string
    assert Severity.HIGH >= "medium"
    assert Severity.LOW < "high"

    # Case-insensitive parsing
    assert Severity.from_str("HIGH") == Severity.HIGH
    assert Severity.from_str("medium") == Severity.MEDIUM
    assert Severity.from_str(" Critical ") == Severity.CRITICAL

    with pytest.raises(ValueError, match="Invalid severity level"):
        Severity.from_str("super-critical")


# ==============================================================================
# 2. Policy Parsing & Schema Validation Tests
# ==============================================================================

def test_policy_loader_missing_file(tmp_path):
    policy = PolicyLoader.load_from_workspace(tmp_path)
    assert policy.is_valid is True
    assert policy.source == "default"
    assert policy.policy.enabled is True
    assert policy.policy.minimum_severity == Severity.MEDIUM
    assert policy.policy.auto_remediate is True
    assert policy.policy.auto_create_pr is True
    assert "main" in policy.policy.target_branches


def test_policy_loader_valid_yaml(tmp_path):
    yaml_content = """
version: "1.0"
policy:
  enabled: true
  minimum_severity: high
  auto_remediate: true
  auto_create_pr: false
  target_branches:
    - main
    - release/*
  allowed_events:
    - pull_request
rules:
  python.sql-injection:
    enabled: true
    auto_remediate: true
  python.command-injection:
    enabled: false
"""
    policy_file = tmp_path / ".patchproof.yml"
    policy_file.write_text(yaml_content)

    policy = PolicyLoader.load_from_workspace(tmp_path)
    assert policy.is_valid is True
    assert policy.source == ".patchproof.yml"
    assert policy.policy.minimum_severity == Severity.HIGH
    assert policy.policy.auto_create_pr is False
    assert policy.policy.target_branches == ["main", "release/*"]
    assert policy.policy.allowed_events == ["pull_request"]
    assert "python.sql-injection" in policy.rules
    assert policy.rules["python.sql-injection"].enabled is True
    assert policy.rules["python.command-injection"].enabled is False


def test_policy_loader_invalid_yaml_syntax(tmp_path):
    policy_file = tmp_path / ".patchproof.yml"
    policy_file.write_text("policy: enabled: [invalid yaml {")

    policy = PolicyLoader.load_from_workspace(tmp_path)
    assert policy.is_valid is False
    assert "Invalid YAML syntax" in (policy.validation_error or "")


def test_policy_loader_invalid_schema_types():
    # enabled not boolean
    p1 = PolicyLoader.parse_yaml("policy:\n  enabled: 'yes'")
    assert p1.is_valid is False
    assert "must be a boolean" in (p1.validation_error or "")

    # minimum_severity invalid
    p2 = PolicyLoader.parse_yaml("policy:\n  minimum_severity: 'fatal'")
    assert p2.is_valid is False
    assert "Invalid 'policy.minimum_severity'" in (p2.validation_error or "")

    # target_branches not list of strings
    p3 = PolicyLoader.parse_yaml("policy:\n  target_branches: 'main'")
    assert p3.is_valid is False
    assert "must be a list of strings" in (p3.validation_error or "")

    # rules invalid
    p4 = PolicyLoader.parse_yaml("rules:\n  rule-1: 'enabled'")
    assert p4.is_valid is False
    assert "must be a mapping" in (p4.validation_error or "")


# ==============================================================================
# 3. Policy Evaluator & Rule Engine Tests
# ==============================================================================

def test_evaluator_policy_disabled():
    policy = RepositoryPolicy(policy=GlobalPolicy(enabled=False))
    decision = PolicyEvaluator.evaluate_event(policy, event_type="pull_request", branch="main")
    assert decision.allowed is False
    assert decision.action == "skip_policy_disabled"


def test_evaluator_event_not_allowed():
    policy = RepositoryPolicy(policy=GlobalPolicy(allowed_events=["pull_request"]))
    decision = PolicyEvaluator.evaluate_event(policy, event_type="code_scanning_alert", branch="main")
    assert decision.allowed is False
    assert decision.action == "skip_event_not_allowed"


def test_evaluator_branch_filtering():
    policy = RepositoryPolicy(policy=GlobalPolicy(target_branches=["main", "release/*"]))

    # Allowed exact
    d1 = PolicyEvaluator.evaluate_event(policy, event_type="pull_request", branch="main")
    assert d1.allowed is True

    # Allowed glob
    d2 = PolicyEvaluator.evaluate_event(policy, event_type="pull_request", branch="release/v1.0")
    assert d2.allowed is True

    # Allowed with refs/heads/
    d3 = PolicyEvaluator.evaluate_event(policy, event_type="pull_request", branch="refs/heads/main")
    assert d3.allowed is True

    # Disallowed branch
    d4 = PolicyEvaluator.evaluate_event(policy, event_type="pull_request", branch="feature/experiment")
    assert d4.allowed is False
    assert d4.action == "skip_branch_not_targeted"


def test_evaluator_finding_severity_threshold():
    policy = RepositoryPolicy(policy=GlobalPolicy(minimum_severity=Severity.HIGH))

    # High finding allowed
    high_finding = {"rule_id": "rule-1", "severity": "HIGH"}
    d1 = PolicyEvaluator.evaluate_finding(policy, high_finding, event_type="pull_request", branch="main")
    assert d1.allowed is True

    # Critical finding allowed
    crit_finding = {"rule_id": "rule-1", "severity": "CRITICAL"}
    d2 = PolicyEvaluator.evaluate_finding(policy, crit_finding, event_type="pull_request", branch="main")
    assert d2.allowed is True

    # Low finding rejected
    low_finding = {"rule_id": "rule-1", "severity": "LOW"}
    d3 = PolicyEvaluator.evaluate_finding(policy, low_finding, event_type="pull_request", branch="main")
    assert d3.allowed is False
    assert d3.action == "skip_severity_too_low"


def test_evaluator_rule_disabled_and_override():
    policy = RepositoryPolicy(
        policy=GlobalPolicy(auto_remediate=True),
        rules={
            "python.sql-injection": RulePolicy(enabled=True, auto_remediate=True),
            "python.disabled-rule": RulePolicy(enabled=False),
            "python.no-auto-rem": RulePolicy(enabled=True, auto_remediate=False),
        },
    )

    # Disabled rule
    d1 = PolicyEvaluator.evaluate_finding(policy, {"rule_id": "python.disabled-rule", "severity": "HIGH"})
    assert d1.allowed is False
    assert d1.action == "skip_rule_disabled"

    # Per-rule auto_remediate disabled
    d2 = PolicyEvaluator.evaluate_finding(policy, {"rule_id": "python.no-auto-rem", "severity": "HIGH"})
    assert d2.allowed is False
    assert d2.action == "skip_auto_remediate_disabled"


def test_evaluator_auto_create_pr_flag():
    policy = RepositoryPolicy(policy=GlobalPolicy(auto_create_pr=False))
    decision = PolicyEvaluator.evaluate_finding(
        policy, {"rule_id": "python.sql-injection", "severity": "HIGH"}
    )
    assert decision.allowed is True
    assert decision.auto_create_pr is False
    assert decision.action == "remediate_only"


# ==============================================================================
# 4. Pipeline Integration & Check Run Tests
# ==============================================================================

class MockCheckRunTransport:
    def __init__(self):
        self.check_runs: dict[int, dict[str, Any]] = {}
        self.calls: list[dict[str, Any]] = []
        self.next_id = 2000

    def create_check_run(self, **kwargs):
        cr_id = self.next_id
        self.next_id += 1
        record = {"id": cr_id, **kwargs}
        self.check_runs[cr_id] = record
        self.calls.append({"action": "create", "id": cr_id, "record": record})
        return record

    def update_check_run(self, check_run_id, **kwargs):
        record = self.check_runs.setdefault(check_run_id, {"id": check_run_id})
        record.update(kwargs)
        self.calls.append({"action": "update", "id": check_run_id, "record": record})
        return record


class MockAuth:
    def installation_token(self, inst_id: int):
        from packages.github.auth import InstallationToken
        return InstallationToken(token="ghs_mock_tok", expires_at=int(1e9))


def _init_git_repo(path: Path) -> str:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    (path / "app.py").write_text(
        "def query_user(user_input: str):\n"
        "    query = f\"SELECT * FROM users WHERE username = '{user_input}'\"\n"
        "    return query\n"
    )
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@test.local", "commit", "-qm", "initial"],
        cwd=path,
        check=True,
    )
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=path, text=True).strip()


def test_pipeline_policy_blocked_branch(tmp_path):
    """Test that a branch disallowed by policy skips remediation and updates Check Run with policy block."""
    repo = tmp_path / "repo_blocked_branch"
    head_sha = _init_git_repo(repo)

    # Add policy allowing only main
    (repo / ".patchproof.yml").write_text(
        "policy:\n  target_branches:\n    - main\n"
    )
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@test.local", "commit", "-qm", "add policy"],
        cwd=repo,
        check=True,
    )
    head_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()

    transport = MockCheckRunTransport()
    reporter = GitHubCheckRunReporter(client=GitHubAppClient(auth=MockAuth(), transport=transport))
    store = InMemoryJobStore()

    job = JobRecord(
        job_id="job-policy-branch-skip",
        repository=str(repo),
        delivery_id="deliv-p1",
        commit_sha=head_sha,
        target_branch="feature/unsupported",
    )
    store.create(job)

    orchestrator = create_concrete_remediation_orchestrator(
        store=store,
        check_run_reporter=reporter,
    )

    res = orchestrator.run(job.job_id)
    assert res["state"] == JobState.FAILED.value
    assert res["verified"] is False
    assert "target_branches" in res["error"]

    # Check Run was updated to neutral / skipped
    assert len(transport.calls) >= 2
    last = transport.calls[-1]["record"]
    assert last["conclusion"] == "neutral"
    assert "skip_branch_not_targeted" in last["output"]["text"]


def test_pipeline_auto_create_pr_disabled(tmp_path):
    """Test that auto_create_pr: false verifies patch, signs evidence, but does not publish PR."""
    repo = tmp_path / "repo_no_pr"
    head_sha = _init_git_repo(repo)

    (repo / ".patchproof.yml").write_text(
        "policy:\n  auto_create_pr: false\n"
    )
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@test.local", "commit", "-qm", "add policy"],
        cwd=repo,
        check=True,
    )
    head_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()

    transport = MockCheckRunTransport()
    reporter = GitHubCheckRunReporter(client=GitHubAppClient(auth=MockAuth(), transport=transport))
    store = InMemoryJobStore()

    class FailIfCalledPublisher:
        def create_pull_request(self, **kwargs):
            pytest.fail("Publisher create_pull_request should NOT be called when auto_create_pr is false")

    job = JobRecord(
        job_id="job-policy-no-pr",
        repository=str(repo),
        delivery_id="deliv-p2",
        commit_sha=head_sha,
        target_branch="main",
    )
    store.create(job)

    orchestrator = create_concrete_remediation_orchestrator(
        store=store,
        github_client=FailIfCalledPublisher(),
        check_run_reporter=reporter,
    )

    res = orchestrator.run(job.job_id)
    assert res["state"] == JobState.VERIFIED.value
    assert res["verified"] is True
    assert res["pr"] is None
    assert res["evidence"] is not None
    assert res["policy"]["auto_create_pr"] is False

    # Check run success summary notes PR disabled by policy
    last = transport.calls[-1]["record"]
    assert last["status"] == "completed"
    assert last["conclusion"] == "success"
    assert "auto_create_pr: false" in last["output"]["text"]


def test_pipeline_invalid_policy_fails_closed(tmp_path):
    """Test that an invalid policy file fails closed safely without leaking secrets."""
    repo = tmp_path / "repo_invalid_policy"
    head_sha = _init_git_repo(repo)

    (repo / ".patchproof.yml").write_text("policy:\n  minimum_severity: invalid-sev-level\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@test.local", "commit", "-qm", "invalid policy"],
        cwd=repo,
        check=True,
    )
    head_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()

    transport = MockCheckRunTransport()
    reporter = GitHubCheckRunReporter(client=GitHubAppClient(auth=MockAuth(), transport=transport))
    store = InMemoryJobStore()

    job = JobRecord(
        job_id="job-policy-invalid",
        repository=str(repo),
        delivery_id="deliv-p3",
        commit_sha=head_sha,
    )
    store.create(job)

    orchestrator = create_concrete_remediation_orchestrator(
        store=store,
        check_run_reporter=reporter,
    )

    res = orchestrator.run(job.job_id)
    assert res["state"] == JobState.FAILED.value
    assert "blocked_invalid_policy" == res["policy"]["action"]


def test_postgres_store_policy_decision():
    """Test persistence of policy decision and target_branch in PostgresJobStore."""
    store = PostgresJobStore("sqlite:///:memory:")
    store.create_schema()

    policy_dec = {
        "allowed": True,
        "action": "remediate_and_publish",
        "reason": "Policy approved",
        "policy_source": ".patchproof.yml",
    }

    job = store.create_from_webhook(
        delivery_id="deliv-pg-policy-01",
        repository="acme/policy-repo",
        commit_sha="a" * 40,
        event_type="pull_request",
        target_branch="main",
        policy_decision=policy_dec,
    )

    assert job.target_branch == "main"
    assert job.policy_decision == policy_dec

    retrieved = store.get(job.job_id)
    assert retrieved is not None
    assert retrieved.target_branch == "main"
    assert retrieved.policy_decision == policy_dec
