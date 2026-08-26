from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from packages.orchestration.remediation import RemediationInput, RemediationOrchestrator
from packages.persistence.models import JobState
from packages.queue.models import RemediationTask
from packages.verification import VerificationPlan


class TaskQueue(Protocol):
    def dequeue(self) -> RemediationTask | None: ...


class JobStore(Protocol):
    def get(self, job_id: str): ...
    def transition(self, job_id: str, state: JobState): ...


@dataclass
class Worker:
    queue: TaskQueue
    jobs: JobStore
    orchestrator: RemediationOrchestrator

    async def process_one(self, *, workspace: str) -> bool:
        task = self.queue.dequeue()
        if task is None:
            return False

        job = self.jobs.get(task.job_id)
        if job is None:
            return False

        request = RemediationInput(
            workspace=workspace,
            rule_id=task.rule_id,
            path=task.path,
            start_line=task.start_line,
            end_line=task.end_line,
            severity=task.severity,
            finding_fingerprint=task.finding_fingerprint,
            verification_plan=VerificationPlan(
                baseline_exploit=["true"],
                patched_exploit=["false"],
                test_command=["true"],
                semgrep_command=["semgrep", "--config", "p/security-audit", "--json", "."],
                finding_fingerprint=task.finding_fingerprint,
            ),
        )

        await self.orchestrator.run(job, request)
        return True
