from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from packages.github.auth import sanitize_secret_text
from packages.github.transport import GitHubAPIError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CheckRunRef:
    id: int
    name: str
    head_sha: str
    status: str  # "queued" | "in_progress" | "completed"
    conclusion: str | None = None  # "success" | "failure" | "neutral" | "cancelled" | "timed_out" | "action_required"
    html_url: str | None = None
    url: str | None = None
    details_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "head_sha": self.head_sha,
            "status": self.status,
        }
        if self.conclusion:
            d["conclusion"] = self.conclusion
        if self.html_url:
            d["html_url"] = self.html_url
        if self.url:
            d["url"] = self.url
        if self.details_url:
            d["details_url"] = self.details_url
        return d


class CheckRunReporter:
    """Base interface for reporting check run status updates to GitHub."""

    def report_queued(self, job: Any) -> CheckRunRef | None:
        raise NotImplementedError

    def report_in_progress(self, job: Any, check_run_id: int | None = None) -> CheckRunRef | None:
        raise NotImplementedError

    def report_success(
        self,
        job: Any,
        *,
        check_run_id: int | None = None,
        pr: dict[str, Any] | None = None,
        evidence: dict[str, Any] | None = None,
        verification: Any = None,
    ) -> CheckRunRef | None:
        raise NotImplementedError

    def report_failure(
        self,
        job: Any,
        *,
        check_run_id: int | None = None,
        stage: str = "remediation",
        error: str = "Remediation failed",
        verification: Any = None,
    ) -> CheckRunRef | None:
        raise NotImplementedError

    def report_policy_block(
        self,
        job: Any,
        *,
        check_run_id: int | None = None,
        decision: Any = None,
    ) -> CheckRunRef | None:
        raise NotImplementedError


class NullCheckRunReporter(CheckRunReporter):
    """No-op reporter used when check run integration is disabled or unauthenticated."""

    def report_queued(self, job: Any) -> CheckRunRef | None:
        return None

    def report_in_progress(self, job: Any, check_run_id: int | None = None) -> CheckRunRef | None:
        return None

    def report_success(
        self,
        job: Any,
        *,
        check_run_id: int | None = None,
        pr: dict[str, Any] | None = None,
        evidence: dict[str, Any] | None = None,
        verification: Any = None,
    ) -> CheckRunRef | None:
        return None

    def report_failure(
        self,
        job: Any,
        *,
        check_run_id: int | None = None,
        stage: str = "remediation",
        error: str = "Remediation failed",
        verification: Any = None,
    ) -> CheckRunRef | None:
        return None

    def report_policy_block(
        self,
        job: Any,
        *,
        check_run_id: int | None = None,
        decision: Any = None,
    ) -> CheckRunRef | None:
        return None


class GitHubCheckRunReporter(CheckRunReporter):
    """Production GitHub App Check Run lifecycle reporter."""

    CHECK_NAME = "PatchProof Security Remediation"

    def __init__(self, client: Any) -> None:
        self.client = client

    def report_queued(self, job: Any) -> CheckRunRef | None:
        """Create initial Check Run with status 'queued'."""
        if not self.client or not getattr(job, "repository", None) or not getattr(job, "commit_sha", None):
            return None

        inst_id = getattr(job, "installation_id", None)
        title = "PatchProof Remediation Queued"
        summary = "Automated code audit and security remediation job has been accepted and queued for analysis."

        output = {
            "title": title,
            "summary": summary,
            "text": f"Job `{job.job_id}` queued for repository `{job.repository}` at commit `{job.commit_sha[:8]}`.",
        }

        try:
            return self.client.create_check_run(
                repository=job.repository,
                head_sha=job.commit_sha,
                name=self.CHECK_NAME,
                status="queued",
                installation_id=inst_id,
                external_id=getattr(job, "job_id", None),
                output=output,
            )
        except Exception as exc:
            sanitized = sanitize_secret_text(str(exc))
            logger.warning("Failed to report Check Run queued status for job %s: %s", getattr(job, "job_id", "?"), sanitized)
            return None

    def report_in_progress(self, job: Any, check_run_id: int | None = None) -> CheckRunRef | None:
        """Update Check Run status to 'in_progress'."""
        if not self.client or not getattr(job, "repository", None):
            return None

        target_id = check_run_id or getattr(job, "check_run_id", None)
        inst_id = getattr(job, "installation_id", None)

        title = "PatchProof Remediation In Progress"
        summary = "Analyzing repository AST and generating verified security patches in isolated sandbox."
        output = {
            "title": title,
            "summary": summary,
            "text": f"Remediation pipeline running for job `{job.job_id}`.",
        }

        try:
            if target_id:
                return self.client.update_check_run(
                    repository=job.repository,
                    check_run_id=target_id,
                    status="in_progress",
                    installation_id=inst_id,
                    output=output,
                )
            else:
                return self.client.create_check_run(
                    repository=job.repository,
                    head_sha=job.commit_sha,
                    name=self.CHECK_NAME,
                    status="in_progress",
                    installation_id=inst_id,
                    external_id=getattr(job, "job_id", None),
                    output=output,
                )
        except Exception as exc:
            sanitized = sanitize_secret_text(str(exc))
            logger.warning("Failed to report Check Run in_progress status for job %s: %s", getattr(job, "job_id", "?"), sanitized)
            return None

    def report_success(
        self,
        job: Any,
        *,
        check_run_id: int | None = None,
        pr: dict[str, Any] | None = None,
        evidence: dict[str, Any] | None = None,
        verification: Any = None,
    ) -> CheckRunRef | None:
        """Update Check Run status to 'completed' with conclusion 'success'."""
        if not self.client or not getattr(job, "repository", None):
            return None

        target_id = check_run_id or getattr(job, "check_run_id", None)
        inst_id = getattr(job, "installation_id", None)
        completed_at = datetime.now(timezone.utc).isoformat()

        title = "PatchProof: Remediation Verified"
        if pr and isinstance(pr, dict):
            summary = "PatchProof automated remediation completed and passed all verification gates."
        else:
            summary = "PatchProof automated remediation completed and passed verification gates (PR creation disabled by policy)."

        text_lines = [
            "### PatchProof Remediation Summary",
            "",
            "- **Status**: ✅ Verification Passed",
        ]

        if evidence and isinstance(evidence, dict):
            target = evidence.get("target_finding", {})
            if target and isinstance(target, dict):
                rule_id = target.get("rule_id", "security-issue")
                severity = target.get("severity", "HIGH")
                text_lines.append(f"- **Vulnerability Remediated**: `{rule_id}` ({severity})")

            v_results = evidence.get("verification_results", {})
            if v_results and isinstance(v_results, dict):
                test_summary = v_results.get("test_summary", "AST syntax valid; 0 residual findings.")
                text_lines.append(f"- **Verification Details**: {test_summary}")

            digest = evidence.get("sha256_digest")
            key_id = evidence.get("signing_key_id", "default")
            algo = evidence.get("signing_algorithm", "ed25519")
            if digest:
                text_lines.append(f"- **Signed Evidence Digest**: `{digest}` (Algorithm: `{algo}`, Key ID: `{key_id}`)")

        if pr and isinstance(pr, dict):
            pr_num = pr.get("number")
            pr_url = pr.get("url") or pr.get("html_url")
            if pr_url:
                text_lines.append(f"- **Remediation Pull Request**: [#{pr_num or 'PR'}]({pr_url})")
        else:
            text_lines.append("- **Pull Request**: Skipped by repository policy (`auto_create_pr: false`)")

        output = {
            "title": title,
            "summary": summary,
            "text": "\n".join(text_lines),
        }

        try:
            if target_id:
                return self.client.update_check_run(
                    repository=job.repository,
                    check_run_id=target_id,
                    status="completed",
                    conclusion="success",
                    completed_at=completed_at,
                    installation_id=inst_id,
                    output=output,
                )
            else:
                return self.client.create_check_run(
                    repository=job.repository,
                    head_sha=job.commit_sha,
                    name=self.CHECK_NAME,
                    status="completed",
                    conclusion="success",
                    completed_at=completed_at,
                    installation_id=inst_id,
                    external_id=getattr(job, "job_id", None),
                    output=output,
                )
        except Exception as exc:
            sanitized = sanitize_secret_text(str(exc))
            logger.warning("Failed to report Check Run success status for job %s: %s", getattr(job, "job_id", "?"), sanitized)
            return None

    def report_policy_block(
        self,
        job: Any,
        *,
        check_run_id: int | None = None,
        decision: Any = None,
    ) -> CheckRunRef | None:
        """Update Check Run status to 'completed' with conclusion 'neutral' or 'failure' on policy block."""
        if not self.client or not getattr(job, "repository", None):
            return None

        target_id = check_run_id or getattr(job, "check_run_id", None)
        inst_id = getattr(job, "installation_id", None)
        completed_at = datetime.now(timezone.utc).isoformat()

        reason = getattr(decision, "reason", "Remediation skipped by repository policy") if decision else "Skipped by policy"
        clean_reason = sanitize_secret_text(str(reason))
        action = getattr(decision, "action", "skip_policy") if decision else "skip_policy"
        is_invalid = action == "blocked_invalid_policy"

        conclusion = "failure" if is_invalid else "neutral"
        title = "PatchProof: Blocked by Policy Configuration" if is_invalid else "PatchProof: Skipped by Security Policy"
        summary = f"Automated remediation was skipped according to repository security policy: {clean_reason}"

        text_lines = [
            "### PatchProof Policy Gate Summary",
            "",
            f"- **Policy Decision**: `{action}`",
            f"- **Reason**: {clean_reason}",
        ]

        if decision:
            src = getattr(decision, "policy_source", ".patchproof.yml")
            text_lines.append(f"- **Policy Source**: `{src}`")
            if getattr(decision, "rule_id", None):
                text_lines.append(f"- **Evaluated Rule**: `{decision.rule_id}`")
            if getattr(decision, "severity", None):
                text_lines.append(f"- **Evaluated Severity**: `{decision.severity}`")
            if getattr(decision, "target_branch", None):
                text_lines.append(f"- **Target Branch**: `{decision.target_branch}`")
            if getattr(decision, "event_type", None):
                text_lines.append(f"- **Event Type**: `{decision.event_type}`")

        output = {
            "title": title,
            "summary": summary,
            "text": "\n".join(text_lines),
        }

        try:
            if target_id:
                return self.client.update_check_run(
                    repository=job.repository,
                    check_run_id=target_id,
                    status="completed",
                    conclusion=conclusion,
                    completed_at=completed_at,
                    installation_id=inst_id,
                    output=output,
                )
            else:
                return self.client.create_check_run(
                    repository=job.repository,
                    head_sha=job.commit_sha,
                    name=self.CHECK_NAME,
                    status="completed",
                    conclusion=conclusion,
                    completed_at=completed_at,
                    installation_id=inst_id,
                    external_id=getattr(job, "job_id", None),
                    output=output,
                )
        except Exception as exc:
            sanitized = sanitize_secret_text(str(exc))
            logger.warning("Failed to report Check Run policy block for job %s: %s", getattr(job, "job_id", "?"), sanitized)
            return None

    def report_failure(
        self,
        job: Any,
        *,
        check_run_id: int | None = None,
        stage: str = "remediation",
        error: str = "Remediation failed",
        verification: Any = None,
    ) -> CheckRunRef | None:
        """Update Check Run status to 'completed' with conclusion 'failure'."""
        if not self.client or not getattr(job, "repository", None):
            return None

        target_id = check_run_id or getattr(job, "check_run_id", None)
        inst_id = getattr(job, "installation_id", None)
        completed_at = datetime.now(timezone.utc).isoformat()

        clean_err = sanitize_secret_text(error)
        title = "PatchProof: Remediation Failed"
        summary = f"Automated security remediation did not succeed during stage '{stage}'."

        text_lines = [
            "### PatchProof Remediation Failure",
            "",
            f"- **Failed Stage**: `{stage}`",
            f"- **Reason**: {clean_err}",
        ]

        if verification is not None:
            v_summary = getattr(verification, "test_summary", None)
            if v_summary:
                text_lines.append(f"- **Verification Details**: {sanitize_secret_text(str(v_summary))}")

        output = {
            "title": title,
            "summary": summary,
            "text": "\n".join(text_lines),
        }

        try:
            if target_id:
                return self.client.update_check_run(
                    repository=job.repository,
                    check_run_id=target_id,
                    status="completed",
                    conclusion="failure",
                    completed_at=completed_at,
                    installation_id=inst_id,
                    output=output,
                )
            else:
                return self.client.create_check_run(
                    repository=job.repository,
                    head_sha=job.commit_sha,
                    name=self.CHECK_NAME,
                    status="completed",
                    conclusion="failure",
                    completed_at=completed_at,
                    installation_id=inst_id,
                    external_id=getattr(job, "job_id", None),
                    output=output,
                )
        except Exception as exc:
            sanitized = sanitize_secret_text(str(exc))
            logger.warning("Failed to report Check Run failure status for job %s: %s", getattr(job, "job_id", "?"), sanitized)
            return None
