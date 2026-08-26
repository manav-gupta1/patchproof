import hashlib
import pytest

from packages.github.e2e import VerifiedPublicationService
from packages.github.publisher import VerificationEvidence, PublicationDenied
from packages.jobs.state import JobState


DIFF = "diff --git a/app.py b/app.py\n"


class Store:
    def __init__(self, state):
        self._state = state

    def state(self, job_id):
        return JobState(self._state)


class Auth:
    def installation_token(self, installation_id):
        return type("Token", (), {"token": "installation-token"})()


class Transport:
    def __init__(self):
        self.existing = None
        self.create_calls = 0
        self.fail_after_remote_create = False

    def find_pull_request_by_marker(self, **kwargs):
        return self.existing

    def create_pull_request(self, **kwargs):
        self.create_calls += 1
        result = {"number": 41, "html_url": "https://github.test/pr/41"}
        if self.fail_after_remote_create:
            self.fail_after_remote_create = False
            self.existing = {
                **result,
                "body": kwargs["body"],
            }
            raise TimeoutError("response lost after GitHub accepted request")
        self.existing = {**result, "body": kwargs["body"]}
        return result


class Client:
    def __init__(self, transport):
        self.transport = transport
        self.auth = Auth()

    def create_pull_request(self, **kwargs):
        token = self.auth.installation_token(kwargs["installation_id"]).token
        marker = kwargs["idempotency_key"]
        existing = self.transport.find_pull_request_by_marker(
            token=token,
            owner=kwargs["repository"].split("/", 1)[0],
            repo=kwargs["repository"].split("/", 1)[1],
            marker=marker,
        )
        if existing:
            return existing

        try:
            result = self.transport.create_pull_request(
                token=token,
                owner=kwargs["repository"].split("/", 1)[0],
                repo=kwargs["repository"].split("/", 1)[1],
                head=kwargs["head"],
                base=kwargs["base"],
                title=kwargs["title"],
                body=kwargs["body"],
            )
        except Exception:
            existing = self.transport.find_pull_request_by_marker(
                token=token,
                owner=kwargs["repository"].split("/", 1)[0],
                repo=kwargs["repository"].split("/", 1)[1],
                marker=marker,
            )
            if existing:
                return existing
            raise
        return result


class Job:
    job_id = "job-99"
    repository = "acme/repo"
    commit_sha = "a" * 40


class Patch:
    branch = "patch/job-99"
    base_branch = "main"
    title = "Fix security finding"
    diff = DIFF


def make_evidence():
    return VerificationEvidence(
        verified=True,
        commit_sha=Job.commit_sha,
        patch_sha256=hashlib.sha256(DIFF.encode()).hexdigest(),
        test_summary="all required tests passed",
        scanner_summary="0 remaining findings",
    )


def test_verified_to_github_pr_is_idempotent():
    transport = Transport()
    service = VerifiedPublicationService(
        Store("verified"), Client(transport), installation_id=123
    )

    first = service.publish(job=Job(), patch_result=Patch(), evidence=make_evidence())
    second = service.publish(job=Job(), patch_result=Patch(), evidence=make_evidence())

    assert first["number"] == 41
    assert second["number"] == 41
    assert transport.create_calls == 1


def test_timeout_after_remote_creation_does_not_duplicate():
    transport = Transport()
    transport.fail_after_remote_create = True
    service = VerifiedPublicationService(
        Store("verified"), Client(transport), installation_id=123
    )

    first = service.publish(job=Job(), patch_result=Patch(), evidence=make_evidence())
    second = service.publish(job=Job(), patch_result=Patch(), evidence=make_evidence())

    assert first["number"] == 41
    assert second["number"] == 41
    assert transport.create_calls == 1


@pytest.mark.parametrize("state", ["queued", "scanning", "verifying", "failed"])
def test_every_non_verified_state_is_blocked(state):
    service = VerifiedPublicationService(
        Store(state), Client(Transport()), installation_id=123
    )
    with pytest.raises(PublicationDenied):
        service.publish(job=Job(), patch_result=Patch(), evidence=make_evidence())
