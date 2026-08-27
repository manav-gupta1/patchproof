from __future__ import annotations

from datetime import datetime, timezone
from threading import RLock
from typing import Any


class InMemoryJobStore:
    """Deterministic development store; PostgreSQL adapter follows same contract."""

    def __init__(self):
        self._jobs = {}
        self._deliveries = set()
        self._events = {}
        self._evidence = {}
        self._prs = {}
        self._policy_decisions = {}
        self._repo_policies = {}
        self._repositories = {}
        self._lock = RLock()

    def onboard_repository(
        self,
        repository: str,
        default_branch: str = "main",
        installation_id: int | None = None,
        status: str = "active",
        provider: str = "github",
    ) -> dict[str, Any]:
        clean_repo = repository.strip()
        parts = clean_repo.split("/", 1)
        owner = parts[0] if len(parts) > 1 else ""
        name = parts[1] if len(parts) > 1 else clean_repo
        now = datetime.now(timezone.utc).isoformat()

        with self._lock:
            record = {
                "id": len(self._repositories) + 1,
                "repository": clean_repo,
                "owner": owner,
                "name": name,
                "provider": provider,
                "default_branch": default_branch,
                "installation_id": installation_id,
                "status": status,
                "created_at": self._repositories.get(clean_repo, {}).get("created_at", now),
                "updated_at": now,
            }
            self._repositories[clean_repo] = record
            return record

    def get_repository(self, repository: str) -> dict[str, Any] | None:
        clean_repo = repository.strip()
        with self._lock:
            return self._repositories.get(clean_repo)

    def set_repository_policy(self, repository: str, policy: dict[str, Any]) -> None:
        with self._lock:
            self._repo_policies[repository.strip().lower()] = policy

    def get_repository_policy(self, repository: str) -> dict[str, Any] | None:
        with self._lock:
            return self._repo_policies.get(repository.strip().lower())

    def exists_delivery(self, delivery_id: str) -> bool:
        with self._lock:
            return delivery_id in self._deliveries

    def create(self, job):
        with self._lock:
            if job.job_id in self._jobs:
                return self._jobs[job.job_id]
            if job.delivery_id in self._deliveries:
                for existing in self._jobs.values():
                    if existing.delivery_id == job.delivery_id:
                        return existing
                raise ValueError("duplicate GitHub delivery")
            if not getattr(job, "created_at", None):
                job.created_at = datetime.now(timezone.utc)
            if not getattr(job, "updated_at", None):
                job.updated_at = job.created_at
            self._jobs[job.job_id] = job
            self._deliveries.add(job.delivery_id)
            if job.job_id not in self._events:
                self._events[job.job_id] = [
                    {
                        "id": 1,
                        "from_state": None,
                        "to_state": getattr(job.state, "value", str(job.state)),
                        "message": "created from GitHub webhook",
                        "created_at": job.created_at.isoformat() if hasattr(job.created_at, "isoformat") else str(job.created_at),
                    }
                ]
            return job

    def create_from_webhook(
        self,
        *,
        delivery_id,
        repository,
        commit_sha,
        event_type,
        installation_id=None,
        check_run_id=None,
        target_branch=None,
        policy_decision=None,
    ):
        from packages.jobs.state import JobRecord
        job_id = f"job-{delivery_id}"
        job = JobRecord(
            job_id=job_id,
            delivery_id=delivery_id,
            repository=repository,
            commit_sha=commit_sha,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            installation_id=installation_id,
            check_run_id=check_run_id,
            target_branch=target_branch,
            policy_decision=policy_decision,
        )
        job.event_type = event_type
        return self.create(job)

    def save_policy_decision(self, job_id: str, decision: dict[str, Any]) -> None:
        with self._lock:
            self._policy_decisions[job_id] = decision
            job = self._jobs.get(job_id)
            if job:
                job.policy_decision = decision
                job.updated_at = datetime.now(timezone.utc)

    def get_policy_decision(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            if job_id in self._policy_decisions:
                return self._policy_decisions[job_id]
            job = self._jobs.get(job_id)
            return getattr(job, "policy_decision", None) if job else None

    def save_check_run_id(self, job_id: str, check_run_id: int) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.check_run_id = check_run_id
                job.updated_at = datetime.now(timezone.utc)

    def record_transition(self, job_id: str, from_state: str | None, to_state: str, message: str = ""):
        with self._lock:
            job = self._jobs.get(job_id)
            now = datetime.now(timezone.utc)
            if job is not None:
                from packages.jobs.state import JobState
                job.state = JobState(to_state) if hasattr(JobState, to_state.upper()) else to_state
                job.updated_at = now
                if to_state == "failed" and message:
                    job.error = message
            events = self._events.setdefault(job_id, [])
            events.append(
                {
                    "id": len(events) + 1,
                    "from_state": from_state,
                    "to_state": to_state,
                    "message": message,
                    "created_at": now.isoformat(),
                }
            )

    def save_pr(self, job_id: str, pr: dict[str, Any]) -> None:
        with self._lock:
            self._prs[job_id] = pr
            job = self._jobs.get(job_id)
            if job:
                job.pr = pr
                if isinstance(pr, dict):
                    job.pr_number = pr.get("number")
                    job.pr_url = pr.get("url") or pr.get("html_url")
                    job.remediation_branch = pr.get("branch") or pr.get("head_branch")
                    if pr.get("head_sha"):
                        job.current_head_sha = pr.get("head_sha")
                        job.verified_sha = pr.get("head_sha")
                job.updated_at = datetime.now(timezone.utc)

    def get_pr(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            if job_id in self._prs:
                return self._prs[job_id]
            job = self._jobs.get(job_id)
            return getattr(job, "pr", None) if job else None

    def find_by_pr(self, repository: str, pr_number: int):
        with self._lock:
            for job in self._jobs.values():
                if job.repository == repository:
                    if getattr(job, "pr_number", None) == pr_number:
                        return job
                    pr = getattr(job, "pr", None)
                    if isinstance(pr, dict) and pr.get("number") == pr_number:
                        return job
            return None

    def find_by_branch(self, repository: str, branch: str):
        with self._lock:
            for job in self._jobs.values():
                if job.repository == repository:
                    if getattr(job, "remediation_branch", None) == branch or getattr(job, "target_branch", None) == branch:
                        return job
                    pr = getattr(job, "pr", None)
                    if isinstance(pr, dict) and (pr.get("branch") == branch or pr.get("head_branch") == branch):
                        return job
            return None

    def find_latest_for_repo(self, repository: str):
        with self._lock:
            matches = [j for j in self._jobs.values() if j.repository == repository]
            return matches[-1] if matches else None

    def mark_stale(self, job_id: str, reason: str = "New commits detected on branch", new_sha: str | None = None) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.is_stale = True
                if new_sha:
                    job.current_head_sha = new_sha
                job.updated_at = datetime.now(timezone.utc)

    def mark_merged(self, job_id: str, merge_commit_sha: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.merge_commit_sha = merge_commit_sha
                job.is_stale = False
                job.updated_at = datetime.now(timezone.utc)

    def mark_rolled_back(self, job_id: str, reason: str, invalidated_by_sha: str | None = None) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.is_stale = True
                job.invalidation_reason = reason
                job.invalidated_by_sha = invalidated_by_sha
                job.updated_at = datetime.now(timezone.utc)

    def mark_superseded(self, job_id: str, reason: str, superseded_by_sha: str | None = None) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.is_stale = True
                job.invalidation_reason = reason
                job.invalidated_by_sha = superseded_by_sha
                job.updated_at = datetime.now(timezone.utc)

    def save_evidence(self, job_id: str, evidence: dict[str, Any]) -> None:
        with self._lock:
            self._evidence[job_id] = evidence
            job = self._jobs.get(job_id)
            if job:
                job.evidence = evidence
                if isinstance(evidence, dict) and evidence.get("commit_sha"):
                    job.verified_sha = evidence.get("commit_sha")
                    job.is_stale = False
                job.updated_at = datetime.now(timezone.utc)

    def get_evidence(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            if job_id in self._evidence:
                return self._evidence[job_id]
            job = self._jobs.get(job_id)
            return getattr(job, "evidence", None) if job else None

    def get_events(self, job_id: str) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._events.get(job_id, []))

    def get(self, job_id: str):
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job):
        with self._lock:
            if job.job_id not in self._jobs:
                raise KeyError(job.job_id)
            job.updated_at = datetime.now(timezone.utc)
            self._jobs[job.job_id] = job
            return job

    def all(self):
        with self._lock:
            return list(self._jobs.values())

    def list_jobs(
        self,
        repository: str | None = None,
        state: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Any]:
        with self._lock:
            jobs = list(self._jobs.values())
            if repository:
                jobs = [j for j in jobs if getattr(j, "repository", None) == repository]
            if state:
                state_lower = state.lower()
                jobs = [
                    j for j in jobs
                    if getattr(getattr(j, "state", None), "value", str(getattr(j, "state", ""))).lower() == state_lower
                ]
            # Order newest first
            jobs = sorted(
                jobs,
                key=lambda j: getattr(j, "created_at", None) or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True,
            )
            return jobs[offset : offset + limit] if limit else jobs[offset:]

    def count_jobs(
        self,
        repository: str | None = None,
        state: str | None = None,
    ) -> int:
        with self._lock:
            jobs = list(self._jobs.values())
            if repository:
                jobs = [j for j in jobs if getattr(j, "repository", None) == repository]
            if state:
                state_lower = state.lower()
                jobs = [
                    j for j in jobs
                    if getattr(getattr(j, "state", None), "value", str(getattr(j, "state", ""))).lower() == state_lower
                ]
            return len(jobs)

    def list_repositories(self) -> list[dict[str, Any]]:
        with self._lock:
            repos: dict[str, dict[str, Any]] = {}

            # 1. Registered repositories
            for repo_name, reg in self._repositories.items():
                repos[repo_name] = {
                    "repository": repo_name,
                    "installation_status": "installed" if reg.get("status") == "active" else reg.get("status", "installed"),
                    "total_jobs": 0,
                    "active_jobs": 0,
                    "verified_prs": 0,
                    "failed_jobs": 0,
                    "last_job_id": None,
                    "last_activity": reg.get("created_at"),
                }

            # 2. Inferred from jobs
            for job in self._jobs.values():
                repo_name = getattr(job, "repository", None)
                if not repo_name:
                    continue
                if repo_name not in repos:
                    repos[repo_name] = {
                        "repository": repo_name,
                        "installation_status": "installed",
                        "total_jobs": 0,
                        "active_jobs": 0,
                        "verified_prs": 0,
                        "failed_jobs": 0,
                        "last_job_id": None,
                        "last_activity": None,
                    }
                r = repos[repo_name]
                r["total_jobs"] += 1
                state_val = getattr(getattr(job, "state", None), "value", str(getattr(job, "state", ""))).lower()
                if state_val in {"queued", "scanning", "analyzing", "patching", "verifying"}:
                    r["active_jobs"] += 1
                elif state_val in {"verified", "pr_created", "pr_updated", "pr_merged"}:
                    r["verified_prs"] += 1
                elif state_val == "failed":
                    r["failed_jobs"] += 1

                created_at = getattr(job, "created_at", None)
                if created_at:
                    c_iso = created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at)
                    if not r["last_activity"] or c_iso > r["last_activity"]:
                        r["last_activity"] = c_iso
                        r["last_job_id"] = getattr(job, "job_id", None)

            return sorted(list(repos.values()), key=lambda x: x.get("last_activity") or "", reverse=True)

