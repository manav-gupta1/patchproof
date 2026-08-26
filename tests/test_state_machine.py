import pytest
from packages.jobs.state import JobState, JobStateMachine, InvalidTransition


def test_happy_path():
    sm = JobStateMachine()
    states = [
        JobState.QUEUED, JobState.SCANNING, JobState.ANALYZING,
        JobState.PATCHING, JobState.VERIFYING, JobState.VERIFIED,
        JobState.PR_CREATED,
    ]
    for current, target in zip(states, states[1:]):
        assert sm.transition(current, target) == target


def test_cannot_skip_verification():
    sm = JobStateMachine()
    with pytest.raises(InvalidTransition):
        sm.transition(JobState.PATCHING, JobState.PR_CREATED)


def test_verified_cannot_go_back():
    sm = JobStateMachine()
    with pytest.raises(InvalidTransition):
        sm.transition(JobState.VERIFIED, JobState.PATCHING)


def test_failure_terminal():
    sm = JobStateMachine()
    assert sm.transition(JobState.VERIFYING, JobState.FAILED) == JobState.FAILED
    with pytest.raises(InvalidTransition):
        sm.transition(JobState.FAILED, JobState.QUEUED)
