from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from packages.orchestration.state import JobState, JobStore


@dataclass(frozen=True)
class JobResult:
    job_id: str
    state: JobState
    pr: dict | None
    evidence: dict


class RemediationOrchestrator:
    """
    End-to-end state-machine coordinator.

    Adapters are injected so the orchestration logic can be tested without
    credentials, network access, or executing customer code in this process.
    """

    def __init__(self, store: JobStore, adapters: dict[str, Any]):
        self.store = store
        self.a = adapters

    def run(self, job_id: str, finding: dict, *, verified_override: bool | None = None) -> JobResult:
        job = self.store.create(job_id)
        try:
            context = self.a["context"](finding)
            self.store.transition(job_id, JobState.CONTEXT_READY)

            proposal = self.a["patch"](finding, context)
            self.store.transition(job_id, JobState.PATCH_PROPOSED)

            self.a["validate"](proposal)
            self.store.transition(job_id, JobState.PATCH_VALIDATED)

            self.store.transition(job_id, JobState.VERIFYING)
            verification = self.a["verify"](finding, proposal)

            verified = bool(verification.get("verified"))
            if verified_override is not None:
                verified = bool(verified_override)

            if not verified:
                self.store.reject(job_id, "verification gates failed")
                return JobResult(job_id, JobState.REJECTED, None, verification)

            job.evidence = verification
            self.store.transition(job_id, JobState.VERIFIED)

            self.store.transition(job_id, JobState.PROMOTING)
            promotion = self.a["promote"](proposal, finding, verified=True)

            pr = self.a["pr"](
                promotion=promotion,
                finding=finding,
                verification=verification,
                verified=True,
            )
            self.store.transition(job_id, JobState.PR_CREATED)
            return JobResult(job_id, JobState.PR_CREATED, pr, verification)

        except Exception as exc:
            self.store.reject(job_id, str(exc))
            return JobResult(job_id, JobState.REJECTED, None, {"error": str(exc)})
