import pytest

from packages.evidence import EvidenceStore
from packages.github import FakeGitHubClient, PullRequestPublisher
from packages.orchestration import (
    JobState,
    PipelineServices,
    RemediationJob,
    RemediationPipeline,
)


class Obj:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        return repr(self.__dict__)


class Checkout:
    async def checkout(self, repository, commit_sha):
        return "/tmp/repo"


class Analysis:
    async def analyze(self, repository_path, finding_fingerprint):
        return Obj(
            eligible=True,
            model_provider="test",
            model_name="deterministic",
        )


class Exploit:
    async def prove(self, repository_path, analysis):
        return Obj(reproduced=True)


class Patch:
    async def patch(self, repository_path, analysis, exploit):
        return Obj(files={"app.py": "patched"})


class Verification:
    def __init__(self, verified=True):
        self.verified = verified

    async def verify(self, repository_path, analysis, exploit, patch):
        return Obj(verified=self.verified)


def make_job():
    return RemediationJob(
        id="job-1",
        state=JobState.RECEIVED,
        repository="acme/demo",
        commit_sha="abc123",
        finding_fingerprint="finding-1",
    )


def services(tmp_path, verified=True):
    github = FakeGitHubClient()
    return PipelineServices(
        checkout=Checkout(),
        analysis=Analysis(),
        exploit=Exploit(),
        patch=Patch(),
        verification=Verification(verified),
        evidence_store=EvidenceStore(),
        pr_publisher=PullRequestPublisher(github),
    ), github


@pytest.mark.asyncio
async def test_pipeline_reaches_pr_created(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    services_, github = services(tmp_path)

    result = await RemediationPipeline(services_).run(
        make_job(), owner="acme", repo="demo", base_branch="main"
    )

    assert result.state is JobState.PR_CREATED
    assert result.pull_request_url
    assert result.evidence_id
    assert len(github.pull_requests) == 1


@pytest.mark.asyncio
async def test_pipeline_stops_before_pr_when_verification_fails(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    services_, github = services(tmp_path, verified=False)

    result = await RemediationPipeline(services_).run(
        make_job(), owner="acme", repo="demo", base_branch="main"
    )

    assert result.state is JobState.FAILED
    assert result.failure_code.value == "verification_failed"
    assert len(github.pull_requests) == 0
