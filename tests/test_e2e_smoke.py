from packages.jobs.orchestrator import RemediationOrchestrator
from packages.jobs.state import JobState, JobStateMachine, JobRecord
from packages.jobs.store import InMemoryJobStore


class GitHub:
    def publish_verified(self, **kwargs):
        return {"url": "https://example.invalid/pull/1"}


def test_full_controlled_pipeline():
    store = InMemoryJobStore()
    store.create(JobRecord("e2e", "local/repo", "delivery-e2e", "a"*40))

    class V:
        verified = True

    orchestrator = RemediationOrchestrator(
        store, JobStateMachine(),
        clone=lambda repo, sha: "/tmp/controlled-repo",
        scan=lambda ws: [{"path": "app.py", "check_id": "demo"}],
        analyze=lambda ws, findings: {
            "finding": findings[0],
            "context": {"source": "value = 1\n"},
        },
        patch=lambda ws, proposal: {"patch": "diff --git a/app.py b/app.py\n",
                                     "head_branch": "patchproof/e2e"},
        verify=lambda **kwargs: V(),
        evidence=lambda job, f, p, pr, v: {
            "verified": v.verified, "evidence_id": "e2e-proof"
        },
        github=GitHub(),
    )

    result = orchestrator.run("e2e")
    assert result["state"] == "pr_created"
    assert store.get("e2e").state is JobState.PR_CREATED
