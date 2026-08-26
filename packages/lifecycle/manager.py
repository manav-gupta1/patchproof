from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from packages.jobs.state import JobState

logger = logging.getLogger(__name__)


@dataclass
class LifecycleEventResult:
    handled: bool
    action: str
    job_id: str | None = None
    state: str | None = None
    message: str = ""
    error: str | None = None


class PRLifecycleManager:
    """Manages PR lifecycle state transitions, synchronization, merge tracking, and rollback/supersession."""

    def __init__(self, store: Any, state_machine: Any = None, enqueue: Any = None, check_runs: Any = None):
        self.store = store
        self.state_machine = state_machine
        self.enqueue = enqueue
        self.check_runs = check_runs

    def handle_pull_request(self, payload: dict[str, Any], delivery_id: str) -> LifecycleEventResult:
        action = payload.get("action", "")
        repository = payload.get("repository", {}).get("full_name")
        pr = payload.get("pull_request") or {}
        pr_number = pr.get("number") or payload.get("number")
        head = pr.get("head") or {}
        head_sha = head.get("sha") or pr.get("head_sha")
        head_ref = head.get("ref") or pr.get("head_ref")

        if not repository or not pr_number:
            return LifecycleEventResult(handled=False, action=action, error="missing_repository_or_pr_number")

        # Find existing job matching PR number or branch
        job = None
        if hasattr(self.store, "find_by_pr") and pr_number:
            job = self.store.find_by_pr(repository, pr_number)
        if not job and head_ref and hasattr(self.store, "find_by_branch"):
            job = self.store.find_by_branch(repository, head_ref)
        if not job and hasattr(self.store, "find_latest_for_repo"):
            job = self.store.find_latest_for_repo(repository)

        if action == "synchronize":
            return self._handle_synchronize(job, payload, repository, pr_number, head_sha, delivery_id)
        elif action == "closed":
            return self._handle_closed(job, payload, repository, pr_number)
        elif action == "reopened":
            return self._handle_reopened(job, payload, repository, pr_number, head_sha, delivery_id)
        else:
            return LifecycleEventResult(handled=False, action=action, message=f"unhandled pr action: {action}")

    def _handle_synchronize(
        self,
        job: Any,
        payload: dict[str, Any],
        repository: str,
        pr_number: int,
        head_sha: str,
        delivery_id: str,
    ) -> LifecycleEventResult:
        if not job:
            return LifecycleEventResult(
                handled=False,
                action="synchronize_no_job",
                message=f"No matching remediation job found for PR #{pr_number}",
            )

        # Idempotency check: if current_head_sha is already head_sha and not stale
        if getattr(job, "current_head_sha", None) == head_sha and not getattr(job, "is_stale", False):
            return LifecycleEventResult(
                handled=True,
                action="synchronize_idempotent",
                job_id=job.job_id,
                state=getattr(job.state, "value", str(job.state)),
                message="PR synchronized with identical head SHA; no state change",
            )

        # Mark verification stale
        if hasattr(self.store, "mark_stale"):
            self.store.mark_stale(
                job.job_id,
                reason=f"PR synchronized with new commit {head_sha}",
                new_sha=head_sha,
            )

        # Record transition to PR_UPDATED
        old_state = getattr(job.state, "value", str(job.state))
        if hasattr(self.store, "record_transition"):
            self.store.record_transition(
                job.job_id,
                from_state=old_state,
                to_state=JobState.PR_UPDATED.value,
                message=f"PR #{pr_number} synchronized with new commit {head_sha}; previous verification marked stale",
            )

        job.state = JobState.PR_UPDATED
        job.current_head_sha = head_sha
        job.is_stale = True
        if hasattr(self.store, "update"):
            self.store.update(job)

        # Re-enqueue remediation/verification pipeline for the new SHA
        if self.enqueue:
            try:
                self.enqueue(job.job_id)
            except Exception as e:
                logger.warning(f"Failed to enqueue re-verification for job {job.job_id}: {e}")

        return LifecycleEventResult(
            handled=True,
            action="synchronize",
            job_id=job.job_id,
            state=JobState.PR_UPDATED.value,
            message=f"PR #{pr_number} marked stale and re-enqueued for commit {head_sha}",
        )

    def _handle_closed(
        self,
        job: Any,
        payload: dict[str, Any],
        repository: str,
        pr_number: int,
    ) -> LifecycleEventResult:
        if not job:
            return LifecycleEventResult(
                handled=False,
                action="closed_no_job",
                message=f"No matching remediation job found for PR #{pr_number}",
            )

        pr = payload.get("pull_request") or {}
        is_merged = pr.get("merged", False)
        merge_commit_sha = pr.get("merge_commit_sha") or payload.get("merge_commit_sha")

        old_state = getattr(job.state, "value", str(job.state))
        if is_merged:
            target_state = JobState.PR_MERGED.value
            msg = f"Remediation PR #{pr_number} merged at commit {merge_commit_sha or 'unknown'}"
            if hasattr(self.store, "mark_merged"):
                self.store.mark_merged(job.job_id, merge_commit_sha=merge_commit_sha or "")
        else:
            target_state = JobState.PR_CLOSED.value
            msg = f"Remediation PR #{pr_number} closed without merge"

        if hasattr(self.store, "record_transition"):
            self.store.record_transition(
                job.job_id,
                from_state=old_state,
                to_state=target_state,
                message=msg,
            )

        job.state = JobState(target_state)
        if is_merged and merge_commit_sha:
            job.merge_commit_sha = merge_commit_sha
        if hasattr(self.store, "update"):
            self.store.update(job)

        return LifecycleEventResult(
            handled=True,
            action="merged" if is_merged else "closed",
            job_id=job.job_id,
            state=target_state,
            message=msg,
        )

    def _handle_reopened(
        self,
        job: Any,
        payload: dict[str, Any],
        repository: str,
        pr_number: int,
        head_sha: str,
        delivery_id: str,
    ) -> LifecycleEventResult:
        if not job:
            return LifecycleEventResult(
                handled=False,
                action="reopened_no_job",
                message=f"No matching remediation job found for PR #{pr_number}",
            )

        old_state = getattr(job.state, "value", str(job.state))
        target_state = JobState.PR_UPDATED.value
        msg = f"Remediation PR #{pr_number} reopened; re-evaluating verification status"

        if hasattr(self.store, "mark_stale"):
            self.store.mark_stale(
                job.job_id,
                reason="PR reopened; requiring fresh verification",
                new_sha=head_sha,
            )

        if hasattr(self.store, "record_transition"):
            self.store.record_transition(
                job.job_id,
                from_state=old_state,
                to_state=target_state,
                message=msg,
            )

        job.state = JobState(target_state)
        job.is_stale = True
        if head_sha:
            job.current_head_sha = head_sha
        if hasattr(self.store, "update"):
            self.store.update(job)

        if self.enqueue:
            try:
                self.enqueue(job.job_id)
            except Exception as e:
                logger.warning(f"Failed to enqueue re-evaluation for job {job.job_id}: {e}")

        return LifecycleEventResult(
            handled=True,
            action="reopened",
            job_id=job.job_id,
            state=target_state,
            message=msg,
        )

    def handle_push(self, payload: dict[str, Any], delivery_id: str) -> LifecycleEventResult:
        repository = payload.get("repository", {}).get("full_name")
        ref = payload.get("ref", "")
        deleted = payload.get("deleted", False)
        commits = payload.get("commits", [])

        if not repository:
            return LifecycleEventResult(handled=False, action="push", error="missing_repository")

        branch = ref.replace("refs/heads/", "").strip()

        # Check if a remediation branch was deleted -> mark ROLLED_BACK
        if deleted and branch:
            job = None
            if hasattr(self.store, "find_by_branch"):
                job = self.store.find_by_branch(repository, branch)
            if job:
                return self.rollback_job(
                    job,
                    reason=f"Remediation branch '{branch}' deleted remotely",
                    caused_by_sha=payload.get("after") or "deleted",
                )

        # Check for revert commits in payload
        for c in commits:
            msg = c.get("message", "")
            commit_id = c.get("id")
            if msg.lower().startswith("revert") or "revert" in msg.lower():
                job = None
                if hasattr(self.store, "find_by_branch"):
                    job = self.store.find_by_branch(repository, branch)
                if job:
                    return self.rollback_job(
                        job,
                        reason=f"Revert commit detected: {msg.strip()}",
                        caused_by_sha=commit_id,
                    )

        return LifecycleEventResult(
            handled=True,
            action="push_processed",
            message="Push event processed cleanly",
        )

    def rollback_job(self, job: Any, reason: str, caused_by_sha: str | None = None) -> LifecycleEventResult:
        old_state = getattr(job.state, "value", str(job.state))
        target_state = JobState.ROLLED_BACK.value

        if hasattr(self.store, "mark_rolled_back"):
            self.store.mark_rolled_back(job.job_id, reason=reason, invalidated_by_sha=caused_by_sha)

        if hasattr(self.store, "record_transition"):
            self.store.record_transition(
                job.job_id,
                from_state=old_state,
                to_state=target_state,
                message=f"Remediation rolled back: {reason}",
            )

        job.state = JobState(target_state)
        job.is_stale = True
        job.invalidation_reason = reason
        job.invalidated_by_sha = caused_by_sha
        if hasattr(self.store, "update"):
            self.store.update(job)

        return LifecycleEventResult(
            handled=True,
            action="rolled_back",
            job_id=job.job_id,
            state=target_state,
            message=f"Job {job.job_id} marked as ROLLED_BACK: {reason}",
        )

    def supersede_job(self, job: Any, reason: str, superseded_by_sha: str | None = None) -> LifecycleEventResult:
        old_state = getattr(job.state, "value", str(job.state))
        target_state = JobState.SUPERSEDED.value

        if hasattr(self.store, "mark_superseded"):
            self.store.mark_superseded(job.job_id, reason=reason, superseded_by_sha=superseded_by_sha)

        if hasattr(self.store, "record_transition"):
            self.store.record_transition(
                job.job_id,
                from_state=old_state,
                to_state=target_state,
                message=f"Remediation superseded: {reason}",
            )

        job.state = JobState(target_state)
        job.is_stale = True
        job.invalidation_reason = reason
        job.invalidated_by_sha = superseded_by_sha
        if hasattr(self.store, "update"):
            self.store.update(job)

        return LifecycleEventResult(
            handled=True,
            action="superseded",
            job_id=job.job_id,
            state=target_state,
            message=f"Job {job.job_id} marked as SUPERSEDED: {reason}",
        )
