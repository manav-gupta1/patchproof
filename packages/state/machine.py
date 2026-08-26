from __future__ import annotations

from enum import StrEnum


class JobState(StrEnum):
    RECEIVED = "received"
    TRIAGED = "triaged"
    CONTEXT_BUILT = "context_built"
    PATCH_GENERATED = "patch_generated"
    PATCH_APPLIED = "patch_applied"
    VERIFYING = "verifying"
    REJECTED = "rejected"
    VERIFIED = "verified"
    PR_CREATED = "pr_created"
    MERGED = "merged"


class InvalidTransition(ValueError):
    pass


_ALLOWED: dict[JobState, set[JobState]] = {
    JobState.RECEIVED: {JobState.TRIAGED, JobState.REJECTED},
    JobState.TRIAGED: {JobState.CONTEXT_BUILT, JobState.REJECTED},
    JobState.CONTEXT_BUILT: {JobState.PATCH_GENERATED, JobState.REJECTED},
    JobState.PATCH_GENERATED: {JobState.PATCH_APPLIED, JobState.REJECTED},
    JobState.PATCH_APPLIED: {JobState.VERIFYING, JobState.REJECTED},
    JobState.VERIFYING: {JobState.VERIFIED, JobState.REJECTED},
    JobState.VERIFIED: {JobState.PR_CREATED},
    JobState.PR_CREATED: {JobState.MERGED, JobState.REJECTED},
    JobState.REJECTED: set(),
    JobState.MERGED: set(),
}


class JobStateMachine:
    def __init__(self, job):
        self.job = job

    def transition(self, to_state: JobState, *, actor: str, reason: str):
        current = self.job.state
        if to_state not in _ALLOWED[current]:
            raise InvalidTransition(f"{current.value} -> {to_state.value} is not allowed")
        from packages.state.models import StateTransition
        self.job.transitions.append(
            StateTransition(
                from_state=current,
                to_state=to_state,
                actor=actor,
                reason=reason,
            )
        )
        self.job.state = to_state
        return self.job.state

    @staticmethod
    def allowed_from(state: JobState) -> frozenset[JobState]:
        return frozenset(_ALLOWED[state])
