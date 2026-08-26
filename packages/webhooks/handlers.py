from __future__ import annotations

from typing import Any
from packages.github.installation import InstallationRegistry
from packages.lifecycle.manager import PRLifecycleManager

SUPPORTED_EVENTS = {
    "code_scanning_alert",
    "check_run",
    "pull_request",
    "push",
    "installation",
    "installation_repositories",
}


class WebhookDispatcher:
    def __init__(
        self,
        jobs,
        enqueue,
        check_runs: Any = None,
        lifecycle_manager: Any = None,
        installation_registry: InstallationRegistry | None = None,
    ):
        self.jobs = jobs
        self.enqueue = enqueue
        self.check_runs = check_runs
        self.lifecycle_manager = lifecycle_manager or PRLifecycleManager(
            store=jobs,
            enqueue=enqueue,
            check_runs=check_runs,
        )
        self.installation_registry = installation_registry

    def dispatch(self, event):
        if event.event not in SUPPORTED_EVENTS:
            return {"accepted": False, "reason": "unsupported_event"}

        payload = event.payload
        if self.jobs.exists_delivery(event.delivery_id):
            return {"accepted": True, "duplicate": True}

        # GitHub App Installation lifecycle handling
        if event.event == "installation" and self.installation_registry:
            res = self.installation_registry.handle_installation_event(payload)
            return {"accepted": True, "event": "installation", "result": res}

        if event.event == "installation_repositories" and self.installation_registry:
            res = self.installation_registry.handle_installation_repositories_event(payload)
            return {"accepted": True, "event": "installation_repositories", "result": res}

        # PR Lifecycle Handling (synchronize, closed, reopened)
        if event.event == "pull_request":
            action = payload.get("action", "")
            if action in {"synchronize", "closed", "reopened"}:
                res = self.lifecycle_manager.handle_pull_request(payload, event.delivery_id)
                if res.handled:
                    return {
                        "accepted": True,
                        "job_id": res.job_id,
                        "action": res.action,
                        "state": res.state,
                    }

        # Push Lifecycle Handling (rollback / supersede / branch deletion)
        if event.event == "push":
            res = self.lifecycle_manager.handle_push(payload, event.delivery_id)
            if res.action in {"rolled_back", "superseded"}:
                return {
                    "accepted": True,
                    "job_id": res.job_id,
                    "action": res.action,
                    "state": res.state,
                }

        repository = payload.get("repository", {}).get("full_name")
        pr = payload.get("pull_request") or {}
        pr_head = pr.get("head") or {}
        commit_sha = (
            payload.get("alert", {}).get("most_recent_instance", {}).get("commit_sha")
            or payload.get("check_run", {}).get("head_sha")
            or pr_head.get("sha")
            or pr.get("head_sha")
            or payload.get("commit_sha")
            or payload.get("after")
            or payload.get("head_sha")
            or (f"pr-{pr.get('number')}" if pr.get("number") is not None else None)
            or (f"pr-{payload.get('number')}" if payload.get("number") is not None else None)
        )
        if not repository or not commit_sha:
            return {"accepted": False, "reason": "missing_repository_or_sha"}

        installation = payload.get("installation") or {}
        installation_id = installation.get("id") if isinstance(installation, dict) else None

        if self.installation_registry and installation_id is not None:
            if not self.installation_registry.is_repository_authorized(installation_id, repository):
                return {"accepted": False, "reason": "repository_not_authorized_under_installation"}

        pr_base = pr.get("base") or {}
        check_suite = payload.get("check_run", {}).get("check_suite") or {}
        raw_branch = (
            pr_base.get("ref")
            or payload.get("ref")
            or check_suite.get("head_branch")
            or pr_head.get("ref")
        )
        target_branch = raw_branch.replace("refs/heads/", "").strip() if isinstance(raw_branch, str) else None

        job = self.jobs.create_from_webhook(
            delivery_id=event.delivery_id,
            repository=repository,
            commit_sha=commit_sha,
            event_type=event.event,
            installation_id=installation_id,
            target_branch=target_branch,
        )

        if self.check_runs:
            try:
                check_run_ref = self.check_runs.report_queued(job)
                if check_run_ref and hasattr(check_run_ref, "id"):
                    job.check_run_id = check_run_ref.id
                    if hasattr(self.jobs, "save_check_run_id"):
                        self.jobs.save_check_run_id(job.job_id, check_run_ref.id)
            except Exception:
                pass

        self.enqueue(job.job_id)
        return {"accepted": True, "job_id": job.job_id}
