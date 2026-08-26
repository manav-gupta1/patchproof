import hashlib
from packages.github.publisher import GitHubPublisher, VerificationEvidence


class Store:
    def __init__(self):
        self._state = "verified"
    def state(self, job_id):
        return type("S", (), {"value": self._state})()


class Auth:
    def installation_token(self, installation_id):
        return type("T", (), {"token": "installation-token"})()


class Transport:
    def __init__(self):
        self.created = 0
        self.existing = None
        self.fail_after_remote = True
    def find_pull_request_by_marker(self, **kwargs):
        return self.existing
    def create_pull_request(self, **kwargs):
        self.created += 1
        self.existing = {
            "number": 12,
            "html_url": "https://github.test/pr/12",
            "body": kwargs["body"],
        }
        if self.fail_after_remote:
            self.fail_after_remote = False
            raise TimeoutError("response lost after remote creation")
        return self.existing


def test_verified_publication_survives_timeout_without_duplicate():
    from packages.github.client import GitHubAppClient

    transport = Transport()
    client = GitHubAppClient(Auth(), transport)
    publisher = GitHubPublisher(client, Store(), installation_id=99)

    diff = "security fix\n"
    digest = hashlib.sha256(diff.encode()).hexdigest()
    job = type("Job", (), {
        "job_id": "job-42",
        "repository": "acme/staging",
        "commit_sha": "a" * 40,
    })()
    patch = type("Patch", (), {
        "diff": diff,
        "branch": "patch/job-42",
        "base_branch": "main",
        "title": "Fix verified security finding",
    })()
    evidence = VerificationEvidence(
        verified=True,
        commit_sha=job.commit_sha,
        patch_sha256=digest,
        test_summary="all tests passed",
        scanner_summary="0 remaining findings",
    )

    pr1 = publisher.publish_verified(job=job, patch_result=patch, evidence=evidence)
    pr2 = publisher.publish_verified(job=job, patch_result=patch, evidence=evidence)

    assert pr1["number"] == 12
    assert pr2["number"] == 12
    assert transport.created == 1
