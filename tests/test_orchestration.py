import pytest

from packages.orchestration import (
    FailureCode,
    InvalidTransition,
    JobState,
    JobStateMachine,
    RemediationJob,
)


def job() -> RemediationJob:
    return RemediationJob(
        id="job-1",
        state=JobState.RECEIVED,
        repository="acme/demo",
        commit_sha="abc123",
        finding_fingerprint="finding-1",
    )


def test_valid_state_sequence() -> None:
    sm = JobStateMachine()
    j = job()

    for state in [
        JobState.ANALYZING,
        JobState.EXPLOITING,
        JobState.PATCHING,
        JobState.VERIFYING,
        JobState.VERIFIED,
        JobState.PR_CREATED,
    ]:
        sm.transition(j, state)

    assert j.state is JobState.PR_CREATED


def test_invalid_skip_is_rejected() -> None:
    sm = JobStateMachine()
    j = job()

    with pytest.raises(InvalidTransition):
        sm.transition(j, JobState.VERIFIED)


def test_failed_job_carries_machine_readable_reason() -> None:
    sm = JobStateMachine()
    j = job()

    sm.fail(j, FailureCode.CHECKOUT_FAILED, "checkout unavailable")

    assert j.state is JobState.FAILED
    assert j.failure_code is FailureCode.CHECKOUT_FAILED
    assert j.failure_message == "checkout unavailable"


def test_terminal_pr_state_cannot_be_reused() -> None:
    sm = JobStateMachine()
    j = job()

    for state in [
        JobState.ANALYZING,
        JobState.EXPLOITING,
        JobState.PATCHING,
        JobState.VERIFYING,
        JobState.VERIFIED,
        JobState.PR_CREATED,
    ]:
        sm.transition(j, state)

    with pytest.raises(InvalidTransition):
        sm.transition(j, JobState.FAILED)
