from __future__ import annotations
from enum import Enum


class JobState(str, Enum):
    QUEUED = "queued"
    SCANNING = "scanning"
    ANALYZING = "analyzing"
    PATCHING = "patching"
    VERIFYING = "verifying"
    VERIFIED = "verified"
    PR_CREATED = "pr_created"
    PR_UPDATED = "pr_updated"
    PR_CLOSED = "pr_closed"
    PR_MERGED = "pr_merged"
    SUPERSEDED = "superseded"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


ALLOWED_TRANSITIONS = {
    JobState.QUEUED: {JobState.SCANNING, JobState.FAILED, JobState.SUPERSEDED, JobState.ROLLED_BACK},
    JobState.SCANNING: {JobState.ANALYZING, JobState.VERIFYING, JobState.FAILED, JobState.SUPERSEDED, JobState.ROLLED_BACK},
    JobState.ANALYZING: {JobState.PATCHING, JobState.FAILED, JobState.SUPERSEDED, JobState.ROLLED_BACK},
    JobState.PATCHING: {JobState.VERIFYING, JobState.FAILED, JobState.SUPERSEDED, JobState.ROLLED_BACK},
    JobState.VERIFYING: {JobState.VERIFIED, JobState.FAILED, JobState.SUPERSEDED, JobState.ROLLED_BACK},
    JobState.VERIFIED: {JobState.PR_CREATED, JobState.PR_UPDATED, JobState.FAILED, JobState.SUPERSEDED, JobState.ROLLED_BACK},
    JobState.PR_CREATED: {JobState.PR_UPDATED, JobState.PR_CLOSED, JobState.PR_MERGED, JobState.SUPERSEDED, JobState.ROLLED_BACK, JobState.SCANNING, JobState.FAILED},
    JobState.PR_UPDATED: {JobState.PR_UPDATED, JobState.PR_CLOSED, JobState.PR_MERGED, JobState.SUPERSEDED, JobState.ROLLED_BACK, JobState.SCANNING, JobState.VERIFYING, JobState.VERIFIED, JobState.PR_CREATED, JobState.FAILED},
    JobState.PR_CLOSED: {JobState.SCANNING, JobState.QUEUED, JobState.PR_UPDATED, JobState.SUPERSEDED, JobState.FAILED},
    JobState.PR_MERGED: set(),
    JobState.SUPERSEDED: {JobState.SCANNING, JobState.QUEUED, JobState.FAILED},
    JobState.ROLLED_BACK: {JobState.SCANNING, JobState.QUEUED, JobState.FAILED},
    JobState.FAILED: set(),
}


class InvalidTransition(ValueError):
    pass


class JobRecord:
    def __init__(
        self,
        job_id,
        repository=None,
        delivery_id=None,
        commit_sha=None,
        state=JobState.QUEUED,
        attempt=0,
        error=None,
        created_at=None,
        updated_at=None,
        installation_id=None,
        check_run_id=None,
        target_branch=None,
        policy_decision=None,
        pr_number=None,
        pr_url=None,
        remediation_branch=None,
        current_head_sha=None,
        verified_sha=None,
        merge_commit_sha=None,
        is_stale=False,
        invalidation_reason=None,
        invalidated_by_sha=None,
    ):
        self.job_id = job_id
        self.repository = repository
        self.delivery_id = delivery_id
        self.commit_sha = commit_sha
        self.state = JobState(state)
        self.attempt = attempt
        self.error = error
        self.created_at = created_at
        self.updated_at = updated_at
        self.installation_id = installation_id
        self.check_run_id = check_run_id
        self.target_branch = target_branch
        self.policy_decision = policy_decision
        self.pr_number = pr_number
        self.pr_url = pr_url
        self.remediation_branch = remediation_branch
        self.current_head_sha = current_head_sha or commit_sha
        self.verified_sha = verified_sha or (commit_sha if state in {JobState.VERIFIED, JobState.PR_CREATED} else None)
        self.merge_commit_sha = merge_commit_sha
        self.is_stale = is_stale
        self.invalidation_reason = invalidation_reason
        self.invalidated_by_sha = invalidated_by_sha


class JobStateMachine:
    def __init__(self):
        self._jobs = {}
        self._states = {}

    def create(self, job_id, **kwargs):
        if job_id in self._jobs:
            return self._jobs[job_id]
        job = JobRecord(job_id=job_id, **kwargs)
        self._jobs[job_id] = job
        self._states[job_id] = job.state
        return job

    def state(self, job_id):
        return self._jobs[job_id].state

    def _mark(self, job_id, target):
        job = self._jobs[job_id]
        return self.transition(job, target)

    def mark_scanning(self, job_id):
        return self._mark(job_id, JobState.SCANNING)

    def mark_analyzing(self, job_id):
        return self._mark(job_id, JobState.ANALYZING)

    def mark_patching(self, job_id):
        return self._mark(job_id, JobState.PATCHING)

    def mark_verifying(self, job_id):
        return self._mark(job_id, JobState.VERIFYING)

    def mark_verified(self, job_id):
        return self._mark(job_id, JobState.VERIFIED)

    def mark_pr_created(self, job_id):
        return self._mark(job_id, JobState.PR_CREATED)

    def mark_pr_updated(self, job_id):
        return self._mark(job_id, JobState.PR_UPDATED)

    def mark_pr_closed(self, job_id):
        return self._mark(job_id, JobState.PR_CLOSED)

    def mark_pr_merged(self, job_id):
        return self._mark(job_id, JobState.PR_MERGED)

    def mark_superseded(self, job_id):
        return self._mark(job_id, JobState.SUPERSEDED)

    def mark_rolled_back(self, job_id):
        return self._mark(job_id, JobState.ROLLED_BACK)

    def fail(self, job, error=None):
        if isinstance(job, str):
            record = self._jobs[job]
            if record.state == JobState.FAILED:
                return record
            return self._mark(job, JobState.FAILED) if error is None else self._fail_record(record, error)
        return self._fail_record(job, error)

    def _fail_record(self, job, error):
        if not self.can_transition(job.state, JobState.FAILED):
            raise InvalidTransition(
                f"{job.state.value} -> {JobState.FAILED.value} is not allowed"
            )
        job.state = JobState.FAILED
        job.error = error
        return job

    def can_transition(self, current, target):
        current = JobState(current)
        target = JobState(target)
        return target in ALLOWED_TRANSITIONS[current]

    def transition(self, current, target):
        if isinstance(current, str) and current in self._jobs:
            job = self._jobs[current]
            target = JobState(target)
            if job.state != target and not self.can_transition(job.state, target):
                raise InvalidTransition(
                    f"{job.state.value} -> {target.value} is not allowed"
                )
            job.state = target
            self._states[job.job_id] = job.state
            return job

        if isinstance(current, JobRecord):
            target = JobState(target)
            if current.state != target and not self.can_transition(current.state, target):
                raise InvalidTransition(
                    f"{current.state.value} -> {target.value} is not allowed"
                )
            current.state = target
            self._states[current.job_id] = current.state
            return current

        current = JobState(current)
        target = JobState(target)
        if not self.can_transition(current, target):
            raise InvalidTransition(f"{current.value} -> {target.value} is not allowed")
        return target

