from __future__ import annotations

from typing import Any
import pytest
from fastapi.testclient import TestClient

from packages.api.app import create_app
from packages.github.webhooks import WebhookEvent
from packages.jobs.orchestrator import RemediationOrchestrator
from packages.jobs.pipeline_factory import create_concrete_remediation_orchestrator
from packages.jobs.state import JobRecord, JobState, JobStateMachine
from packages.jobs.store import InMemoryJobStore
from packages.lifecycle.manager import PRLifecycleManager
from packages.store.postgres import PostgresJobStore
from packages.webhooks.handlers import WebhookDispatcher


def _create_mock_job(store, job_id="job-lifecycle-1", repo="acme/service", head_sha="a"*40, pr_num=42):
    job = JobRecord(
        job_id=job_id,
        repository=repo,
        delivery_id=f"deliv-{job_id}",
        commit_sha=head_sha,
        state=JobState.PR_CREATED,
        pr_number=pr_num,
        pr_url=f"https://github.com/{repo}/pull/{pr_num}",
        remediation_branch=f"patchproof/fix-{pr_num}",
        current_head_sha=head_sha,
        verified_sha=head_sha,
        is_stale=False,
    )
    store.create(job)
    store.save_pr(job_id, {
        "number": pr_num,
        "url": f"https://github.com/{repo}/pull/{pr_num}",
        "branch": f"patchproof/fix-{pr_num}",
        "head_sha": head_sha,
        "repository": repo,
    })
    return job


# ==============================================================================
# 1. PR Synchronize Tests
# ==============================================================================

def test_pr_synchronize_marks_old_verification_stale():
    store = InMemoryJobStore()
    enqueued = []
    _create_mock_job(store, job_id="job-sync-1", head_sha="1111"*10, pr_num=10)

    mgr = PRLifecycleManager(store=store, enqueue=lambda jid: enqueued.append(jid))

    payload = {
        "action": "synchronize",
        "repository": {"full_name": "acme/service"},
        "pull_request": {
            "number": 10,
            "head": {"sha": "2222"*10, "ref": "patchproof/fix-10"},
        },
    }

    res = mgr.handle_pull_request(payload, delivery_id="deliv-sync-1")
    assert res.handled is True
    assert res.action == "synchronize"
    assert res.state == JobState.PR_UPDATED.value

    job = store.get("job-sync-1")
    assert job.state == JobState.PR_UPDATED
    assert job.is_stale is True
    assert job.current_head_sha == "2222"*10
    assert job.verified_sha == "1111"*10  # Previous verified SHA remains for audit
    assert "job-sync-1" in enqueued

    # Events audit trail
    events = store.get_events("job-sync-1")
    assert any(e["to_state"] == JobState.PR_UPDATED.value and "synchronized with new commit" in e["message"] for e in events)


def test_pr_synchronize_unchanged_head_is_idempotent():
    store = InMemoryJobStore()
    enqueued = []
    _create_mock_job(store, job_id="job-sync-idempotent", head_sha="1111"*10, pr_num=11)

    mgr = PRLifecycleManager(store=store, enqueue=lambda jid: enqueued.append(jid))

    payload = {
        "action": "synchronize",
        "repository": {"full_name": "acme/service"},
        "pull_request": {
            "number": 11,
            "head": {"sha": "1111"*10, "ref": "patchproof/fix-11"},
        },
    }

    res = mgr.handle_pull_request(payload, delivery_id="deliv-sync-idem")
    assert res.handled is True
    assert res.action == "synchronize_idempotent"
    assert len(enqueued) == 0

    job = store.get("job-sync-idempotent")
    assert job.is_stale is False


# ==============================================================================
# 2. PR Merge & Close & Reopen Tests
# ==============================================================================

def test_pr_merge_transitions_to_pr_merged():
    store = InMemoryJobStore()
    _create_mock_job(store, job_id="job-merge-1", head_sha="1111"*10, pr_num=12)

    mgr = PRLifecycleManager(store=store)

    payload = {
        "action": "closed",
        "repository": {"full_name": "acme/service"},
        "pull_request": {
            "number": 12,
            "merged": True,
            "merge_commit_sha": "9999"*10,
        },
    }

    res = mgr.handle_pull_request(payload, delivery_id="deliv-merge-1")
    assert res.handled is True
    assert res.action == "merged"
    assert res.state == JobState.PR_MERGED.value

    job = store.get("job-merge-1")
    assert job.state == JobState.PR_MERGED
    assert job.merge_commit_sha == "9999"*10

    events = store.get_events("job-merge-1")
    assert any(e["to_state"] == JobState.PR_MERGED.value for e in events)


def test_pr_closed_without_merge_transitions_to_pr_closed():
    store = InMemoryJobStore()
    _create_mock_job(store, job_id="job-closed-1", head_sha="1111"*10, pr_num=13)

    mgr = PRLifecycleManager(store=store)

    payload = {
        "action": "closed",
        "repository": {"full_name": "acme/service"},
        "pull_request": {
            "number": 13,
            "merged": False,
        },
    }

    res = mgr.handle_pull_request(payload, delivery_id="deliv-close-1")
    assert res.handled is True
    assert res.action == "closed"
    assert res.state == JobState.PR_CLOSED.value

    job = store.get("job-closed-1")
    assert job.state == JobState.PR_CLOSED


def test_pr_reopened_marks_stale_and_reenqueues():
    store = InMemoryJobStore()
    enqueued = []
    _create_mock_job(store, job_id="job-reopen-1", head_sha="1111"*10, pr_num=14)

    mgr = PRLifecycleManager(store=store, enqueue=lambda jid: enqueued.append(jid))

    payload = {
        "action": "reopened",
        "repository": {"full_name": "acme/service"},
        "pull_request": {
            "number": 14,
            "head": {"sha": "1111"*10},
        },
    }

    res = mgr.handle_pull_request(payload, delivery_id="deliv-reopen-1")
    assert res.handled is True
    assert res.action == "reopened"
    assert res.state == JobState.PR_UPDATED.value

    job = store.get("job-reopen-1")
    assert job.is_stale is True
    assert "job-reopen-1" in enqueued


# ==============================================================================
# 3. Rollback & Branch Deletion Tests
# ==============================================================================

def test_push_branch_deleted_marks_job_rolled_back():
    store = InMemoryJobStore()
    _create_mock_job(store, job_id="job-del-branch", head_sha="1111"*10, pr_num=15)

    mgr = PRLifecycleManager(store=store)

    payload = {
        "repository": {"full_name": "acme/service"},
        "ref": "refs/heads/patchproof/fix-15",
        "deleted": True,
        "after": "0000"*10,
    }

    res = mgr.handle_push(payload, delivery_id="deliv-push-del")
    assert res.handled is True
    assert res.action == "rolled_back"
    assert res.state == JobState.ROLLED_BACK.value

    job = store.get("job-del-branch")
    assert job.state == JobState.ROLLED_BACK
    assert "deleted remotely" in job.invalidation_reason


def test_push_revert_commit_marks_job_rolled_back():
    store = InMemoryJobStore()
    _create_mock_job(store, job_id="job-revert-commit", head_sha="1111"*10, pr_num=16)

    mgr = PRLifecycleManager(store=store)

    payload = {
        "repository": {"full_name": "acme/service"},
        "ref": "refs/heads/patchproof/fix-16",
        "deleted": False,
        "commits": [
            {
                "id": "rev12345",
                "message": "Revert 'fix(security): remediate sql injection'",
            }
        ],
    }

    res = mgr.handle_push(payload, delivery_id="deliv-push-revert")
    assert res.handled is True
    assert res.action == "rolled_back"
    assert res.state == JobState.ROLLED_BACK.value

    job = store.get("job-revert-commit")
    assert job.state == JobState.ROLLED_BACK
    assert job.invalidated_by_sha == "rev12345"


# ==============================================================================
# 4. Stale Evidence Publication Rejection Tests
# ==============================================================================

def test_stale_evidence_blocks_publication():
    store = InMemoryJobStore()
    job = JobRecord(
        job_id="job-stale-pub",
        repository="acme/service",
        delivery_id="deliv-stale-pub",
        commit_sha="2222"*10,
        current_head_sha="2222"*10,
        verified_sha="1111"*10,
        is_stale=True,  # Stale evidence
    )
    store.create(job)

    class PublisherShouldNotBeCalled:
        def publish_verified(self, **kwargs):
            pytest.fail("Publisher publish_verified should not be called when verification is stale")

    class V:
        verified = True

    orchestrator = RemediationOrchestrator(
        store=store,
        state_machine=JobStateMachine(),
        clone=lambda repo, sha: "/tmp/fake-repo",
        scan=lambda ws: [{"rule_id": "rule-1", "severity": "HIGH"}],
        analyze=lambda ws, f: {"candidate": None, "finding": f[0], "context": None},
        patch=lambda ws, p: {"applied_files": ["app.py"]},
        verify=lambda **kwargs: V(),
        evidence=lambda *args, **kwargs: {"verified": True, "evidence_id": "ev-1", "signature": "sig123"},
        github=PublisherShouldNotBeCalled(),
    )

    res = orchestrator.run("job-stale-pub")
    assert res["state"] == JobState.FAILED.value
    assert "stale verification evidence" in res["error"]


# ==============================================================================
# 5. WebhookDispatcher Integration Tests
# ==============================================================================

def test_webhook_dispatcher_synchronize_and_merge():
    store = InMemoryJobStore()
    enqueued = []
    _create_mock_job(store, job_id="job-wd-1", head_sha="1111"*10, pr_num=20)

    dispatcher = WebhookDispatcher(jobs=store, enqueue=lambda jid: enqueued.append(jid))

    # 1. Synchronize with new commit
    ev_sync = WebhookEvent(
        event="pull_request",
        delivery_id="deliv-wd-sync-1",
        payload={
            "action": "synchronize",
            "repository": {"full_name": "acme/service"},
            "pull_request": {
                "number": 20,
                "head": {"sha": "3333"*10, "ref": "patchproof/fix-20"},
            },
        },
    )
    res_sync = dispatcher.dispatch(ev_sync)
    assert res_sync["accepted"] is True
    assert res_sync["action"] == "synchronize"
    assert res_sync["state"] == JobState.PR_UPDATED.value

    # 2. Closed & Merged
    ev_merge = WebhookEvent(
        event="pull_request",
        delivery_id="deliv-wd-merge-1",
        payload={
            "action": "closed",
            "repository": {"full_name": "acme/service"},
            "pull_request": {
                "number": 20,
                "merged": True,
                "merge_commit_sha": "4444"*10,
            },
        },
    )
    res_merge = dispatcher.dispatch(ev_merge)
    assert res_merge["accepted"] is True
    assert res_merge["action"] == "merged"
    assert res_merge["state"] == JobState.PR_MERGED.value


# ==============================================================================
# 6. Postgres Persistence & REST API Tests
# ==============================================================================

def test_postgres_store_lifecycle_fields():
    store = PostgresJobStore("sqlite:///:memory:")
    store.create_schema()

    job = store.create_from_webhook(
        delivery_id="deliv-pg-life-01",
        repository="acme/pg-repo",
        commit_sha="aaaa"*10,
        event_type="pull_request",
        target_branch="main",
    )

    store.save_pr(job.job_id, {
        "number": 77,
        "url": "https://github.com/acme/pg-repo/pull/77",
        "branch": "patchproof/fix-77",
        "head_sha": "aaaa"*10,
    })

    # Query by PR number
    found = store.find_by_pr("acme/pg-repo", 77)
    assert found is not None
    assert found.job_id == job.job_id
    assert found.pr_number == 77
    assert found.remediation_branch == "patchproof/fix-77"
    assert found.is_stale is False

    # Mark stale
    store.mark_stale(job.job_id, reason="new commit", new_sha="bbbb"*10)
    retrieved = store.get(job.job_id)
    assert retrieved.is_stale is True
    assert retrieved.current_head_sha == "bbbb"*10

    # Mark merged
    store.mark_merged(job.job_id, merge_commit_sha="cccc"*10)
    retrieved2 = store.get(job.job_id)
    assert retrieved2.merge_commit_sha == "cccc"*10
    assert retrieved2.is_stale is False


def test_api_exposes_pr_lifecycle_status():
    store = InMemoryJobStore()
    job = _create_mock_job(store, job_id="job-api-life-1", head_sha="1111"*10, pr_num=99)
    job.is_stale = True
    job.current_head_sha = "2222"*10
    job.merge_commit_sha = "3333"*10

    app = create_app(store=store, webhook_secret="secret", auth_enabled=False)
    client = TestClient(app)

    res = client.get("/jobs/job-api-life-1")
    assert res.status_code == 200
    data = res.json()
    assert data["job_id"] == "job-api-life-1"
    assert data["pr_number"] == 99
    assert data["is_stale"] is True
    assert data["current_head_sha"] == "2222"*10
    assert data["merge_commit_sha"] == "3333"*10
    assert data["remediation_branch"] == "patchproof/fix-99"
