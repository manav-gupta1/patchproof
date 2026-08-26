import hashlib
import pytest

from packages.github.publisher import GitHubPublisher, VerificationEvidence, PublicationDenied


class State:
    def __init__(self, value):
        self.value = value


class Store:
    def __init__(self, state):
        self._state = state

    def state(self, job_id):
        return State(self._state)


class GitHub:
    def __init__(self):
        self.calls = []

    def create_pull_request(self, **kwargs):
        self.calls.append(kwargs)
        return {"number": 7}


class Patch:
    diff = "diff --git a/a.py b/a.py\n"


class Job:
    job_id = "job-1"
    repository = "acme/staging"
    commit_sha = "a" * 40


def evidence(verified=True):
    digest = hashlib.sha256(Patch.diff.encode()).hexdigest()
    return VerificationEvidence(
        verified=verified,
        commit_sha=Job.commit_sha,
        patch_sha256=digest,
        test_summary="12 tests passed",
        scanner_summary="0 remaining findings",
    )


def test_verified_publish():
    gh = GitHub()
    publisher = GitHubPublisher(gh, Store("verified"), installation_id=42)
    result = publisher.publish_verified(job=Job(), patch_result=type(
        "P", (), {"diff": Patch.diff, "branch": "patch/job-1",
                   "base_branch": "main", "title": "Fix security finding"})(),
        evidence=evidence(),
    )
    assert result == {"number": 7}
    assert gh.calls[0]["repository"] == "acme/staging"
    assert "Patch SHA-256" in gh.calls[0]["body"]


@pytest.mark.parametrize("state", ["queued", "verifying", "failed"])
def test_non_verified_state_denied(state):
    publisher = GitHubPublisher(GitHub(), Store(state))
    with pytest.raises(PublicationDenied):
        publisher.publish_verified(
            job=Job(),
            patch_result=type("P", (), {"diff": Patch.diff, "branch": "b",
                                        "base_branch": "main", "title": "x"})(),
            evidence=evidence(),
        )


def test_false_verification_denied():
    publisher = GitHubPublisher(GitHub(), Store("verified"))
    with pytest.raises(PublicationDenied):
        publisher.publish_verified(
            job=Job(),
            patch_result=type("P", (), {"diff": Patch.diff, "branch": "b",
                                        "base_branch": "main", "title": "x"})(),
            evidence=evidence(False),
        )


def test_commit_mismatch_denied():
    publisher = GitHubPublisher(GitHub(), Store("verified"))
    ev = evidence()
    ev = VerificationEvidence(
        True, "b"*40, ev.patch_sha256, ev.test_summary, ev.scanner_summary
    )
    with pytest.raises(PublicationDenied):
        publisher.publish_verified(
            job=Job(),
            patch_result=type("P", (), {"diff": Patch.diff, "branch": "b",
                                        "base_branch": "main", "title": "x"})(),
            evidence=ev,
        )


def test_patch_digest_mismatch_denied():
    publisher = GitHubPublisher(GitHub(), Store("verified"))
    ev = evidence()
    ev = VerificationEvidence(
        True, ev.commit_sha, "0"*64, ev.test_summary, ev.scanner_summary
    )
    with pytest.raises(PublicationDenied):
        publisher.publish_verified(
            job=Job(),
            patch_result=type("P", (), {"diff": Patch.diff, "branch": "b",
                                        "base_branch": "main", "title": "x"})(),
            evidence=ev,
        )
