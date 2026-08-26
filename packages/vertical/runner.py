from __future__ import annotations
from dataclasses import dataclass, asdict

from packages.state import JobState
from packages.patching.validator import PatchValidator
from packages.verification.evidence import verification_evidence


@dataclass(frozen=True)
class VerticalSliceResult:
    job_id: str
    verified: bool
    final_state: str
    evidence_id: str | None
    patch_files: list[str]
    verification: dict

    def as_dict(self):
        return asdict(self)


class VerticalSliceRunner:
    """
    Wires the core remediation path together.

    External adapters (LLM, sandbox, Semgrep, persistence) are injected;
    this runner owns ordering and fail-closed decisions.
    """

    def __init__(self, *, context_extractor, patch_generator,
                 patch_repository, verification_engine, repository):
        self.context_extractor = context_extractor
        self.patch_generator = patch_generator
        self.patch_repository = patch_repository
        self.verification_engine = verification_engine
        self.repository = repository

    def run(self, job, finding, *, baseline_exploit, patched_exploit,
            test_command, semgrep_targets=None):
        # 1. Context
        context = self.context_extractor.extract(finding)

        # 2. Generate structured patch
        proposal = self.patch_generator.generate(finding, context.as_dict())
        proposal.validate_shape()

        # 3. Validate + apply only after git --check succeeds.
        validator = PatchValidator(self.repository)
        validator.apply(proposal)

        # 4. Verify exploit reproduction, exploit blocking, tests, Semgrep.
        report = self.verification_engine.verify(
            baseline_exploit_command=baseline_exploit,
            patched_exploit_command=patched_exploit,
            test_command=test_command,
            semgrep_targets=semgrep_targets,
        )

        evidence = verification_evidence(report)
        evidence_id = self.patch_repository.add_evidence(job.job_id, evidence.kind, evidence.payload)

        if report.verified:
            final_state = JobState.VERIFIED
        else:
            final_state = JobState.REJECTED

        self.patch_repository.transition(
            job,
            to_state=final_state,
            actor="verification",
            reason="all verification gates passed" if report.verified else "verification gate failed",
        )

        return VerticalSliceResult(
            job_id=job.job_id,
            verified=report.verified,
            final_state=job.state.value,
            evidence_id=evidence_id,
            patch_files=list(proposal.changed_files),
            verification=report.as_dict(),
        )
