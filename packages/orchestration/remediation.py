from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from packages.orchestration.models import JobState, RemediationJob
from packages.patching import PatchEngine, PatchProposal
from packages.sandbox import ExecutionRequest, SandboxExecutor
from packages.verification import VerificationReport, VerificationRunner, VerificationPlan


class StateStore(Protocol):
    def transition(self, job_id: str, to_state: JobState) -> None: ...


class EvidenceSink(Protocol):
    def record(self, job_id: str, kind: str, payload: dict) -> str: ...


@dataclass
class RemediationInput:
    workspace: str
    rule_id: str
    path: str
    start_line: int
    end_line: int
    severity: str
    finding_fingerprint: str
    verification_plan: VerificationPlan


@dataclass
class RemediationOutcome:
    job: RemediationJob
    patch: PatchProposal | None
    verification: VerificationReport | None
    evidence_ids: list[str]
    terminal_state: JobState


class InMemoryStateStore:
    def __init__(self) -> None:
        self.jobs: dict[str, RemediationJob] = {}
        self.events: list[tuple[str, JobState]] = []

    def add(self, job: RemediationJob) -> None:
        self.jobs[job.id] = job

    def transition(self, job_id: str, to_state: JobState) -> None:
        job = self.jobs[job_id]
        job.state = to_state
        job.updated_at = datetime.now(timezone.utc)
        self.events.append((job_id, to_state))


class InMemoryEvidenceSink:
    def __init__(self) -> None:
        self.items: list[tuple[str, str, dict]] = []

    def record(self, job_id: str, kind: str, payload: dict) -> str:
        evidence_id = f"evidence-{len(self.items) + 1}"
        self.items.append((job_id, kind, payload))
        return evidence_id


class RemediationOrchestrator:
    """Coordinates generation and external verification.

    The model is never allowed to move a job to VERIFIED. Only the verification
    runner can establish that terminal state.
    """

    def __init__(
        self,
        *,
        patch_engine: PatchEngine,
        verification_runner: VerificationRunner,
        state_store: StateStore,
        evidence_sink: EvidenceSink,
    ) -> None:
        self.patch_engine = patch_engine
        self.verification_runner = verification_runner
        self.state_store = state_store
        self.evidence_sink = evidence_sink

    async def run(
        self,
        job: RemediationJob,
        request: RemediationInput,
    ) -> RemediationOutcome:
        self.state_store.transition(job.id, JobState.ANALYZING)

        evidence_ids: list[str] = []
        patch: PatchProposal | None = None
        verification: VerificationReport | None = None

        try:
            patch = await self.patch_engine.generate_and_apply(
                workspace=request.workspace,
                fingerprint=request.finding_fingerprint,
                rule_id=request.rule_id,
                path=request.path,
                start_line=request.start_line,
                end_line=request.end_line,
                severity=request.severity,
            )

            evidence_ids.append(
                self.evidence_sink.record(
                    job.id,
                    "patch_proposal",
                    {
                        "patch_id": patch.candidate.patch_id,
                        "explanation": patch.candidate.explanation,
                        "changed_files": patch.candidate.changed_files,
                        "model_provider": patch.candidate.model_provider,
                        "model_name": patch.candidate.model_name,
                    },
                )
            )

            self.state_store.transition(job.id, JobState.VERIFYING)

            verification = self.verification_runner.run(
                request.workspace,
                request.verification_plan,
            )

            evidence_ids.append(
                self.evidence_sink.record(
                    job.id,
                    "verification",
                    verification.model_dump(mode="json"),
                )
            )

            if verification.verified:
                self.state_store.transition(job.id, JobState.VERIFIED)
                terminal = JobState.VERIFIED
            else:
                self.state_store.transition(job.id, JobState.FAILED)
                terminal = JobState.FAILED

            return RemediationOutcome(
                job=job,
                patch=patch,
                verification=verification,
                evidence_ids=evidence_ids,
                terminal_state=terminal,
            )
        except Exception as exc:
            evidence_ids.append(
                self.evidence_sink.record(
                    job.id,
                    "orchestrator_error",
                    {"type": type(exc).__name__, "message": str(exc)},
                )
            )
            self.state_store.transition(job.id, JobState.FAILED)
            return RemediationOutcome(
                job=job,
                patch=patch,
                verification=verification,
                evidence_ids=evidence_ids,
                terminal_state=JobState.FAILED,
            )
