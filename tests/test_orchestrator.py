import pytest

from packages.jobs.orchestrator import RemediationOrchestrator
from packages.jobs.state import JobState, JobStateMachine, JobRecord
from packages.jobs.store import InMemoryJobStore
from packages.jobs.adapters import VerifiedGitHubPublisher


def make_job():
    return JobRecord("j1", "acme/demo", "delivery-1", "a" * 40)


class GitHub:
    def __init__(self):
        self.published = 0

    def publish_verified(self, **kwargs):
        self.published += 1
        return {"url": "https://example.test/pr/1"}


def test_verified_pipeline_reaches_pr_created():
    store = InMemoryJobStore()
    store.create(make_job())
    gh = GitHub()
    calls = []

    def stage(name, value=None):
        def fn(*args, **kwargs):
            calls.append(name)
            return value if value is not None else {}
        return fn

    verify = stage("verify", type("V", (), {"verified": True})())
    evidence = lambda *args: {"verified": True, "evidence_id": "abc"}

    runner = RemediationOrchestrator(
        store, JobStateMachine(),
        clone=stage("clone", "/tmp/repo"),
        scan=stage("scan", []),
        analyze=stage("analyze", {}),
        patch=stage("patch", {"head_branch": "patchproof/j1"}),
        verify=verify,
        evidence=evidence,
        github=gh,
    )
    result = runner.run("j1")
    assert result["state"] == "pr_created"
    assert calls == ["clone", "scan", "analyze", "patch", "verify"]
    assert store.get("j1").state is JobState.PR_CREATED
    assert gh.published == 1


def test_failed_verification_never_publishes():
    store = InMemoryJobStore()
    store.create(make_job())
    gh = GitHub()

    runner = RemediationOrchestrator(
        store, JobStateMachine(),
        clone=lambda *a: "/tmp/repo",
        scan=lambda *a: [],
        analyze=lambda *a: {},
        patch=lambda *a: {"head_branch": "patchproof/j1"},
        verify=lambda **kwargs: type("V", (), {"verified": False})(),
        evidence=lambda *args: {"verified": False, "evidence_id": "abc"},
        github=gh,
    )
    result = runner.run("j1")
    assert result["state"] == "failed"
    assert gh.published == 0


def test_publisher_rejects_unverified_evidence():
    publisher = VerifiedGitHubPublisher(object())
    with pytest.raises(PermissionError):
        publisher.publish_verified(
            repository="acme/demo",
            commit_sha="a"*40,
            patch_result={"head_branch": "x"},
            evidence={"verified": False},
        )
