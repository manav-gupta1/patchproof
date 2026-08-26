from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from packages.evidence import EvidenceBuilder, EvidenceKind, EvidenceStore
from packages.github import PullRequestPublisher
from packages.orchestration.models import FailureCode, JobState, RemediationJob
from packages.orchestration.state_machine import JobStateMachine


class CheckoutService(Protocol):
    async def checkout(self, repository: str, commit_sha: str) -> str: ...


class AnalysisService(Protocol):
    async def analyze(self, repository_path: str, finding_fingerprint: str): ...


class ExploitService(Protocol):
    async def prove(self, repository_path: str, analysis): ...


class PatchService(Protocol):
    async def patch(self, repository_path: str, analysis, exploit): ...


class VerificationService(Protocol):
    async def verify(self, repository_path: str, analysis, exploit, patch): ...


@dataclass
class PipelineServices:
    checkout: CheckoutService
    analysis: AnalysisService
    exploit: ExploitService
    patch: PatchService
    verification: VerificationService
    evidence_store: EvidenceStore
    pr_publisher: PullRequestPublisher


class RemediationPipeline:
    """Durable orchestration boundary.

    The concrete services can be backed by workers/queues and isolated
    sandboxes. This layer owns security-critical sequencing and refuses to
    advance after failed gates.
    """

    def __init__(self, services: PipelineServices) -> None:
        self.services = services
        self.sm = JobStateMachine()

    async def run(
        self,
        job: RemediationJob,
        *,
        owner: str,
        repo: str,
        base_branch: str,
    ) -> RemediationJob:
        try:
            self.sm.transition(job, JobState.ANALYZING)
            repo_path = await self.services.checkout.checkout(
                job.repository, job.commit_sha
            )

            analysis = await self.services.analysis.analyze(
                repo_path, job.finding_fingerprint
            )
            if not getattr(analysis, "eligible", True):
                return self.sm.fail(
                    job, FailureCode.NOT_ELIGIBLE, "finding is not eligible for remediation"
                )

            self.sm.transition(job, JobState.EXPLOITING)
            exploit = await self.services.exploit.prove(repo_path, analysis)
            if not getattr(exploit, "reproduced", False):
                return self.sm.fail(
                    job, FailureCode.EXPLOIT_FAILED, "baseline exploit was not reproduced"
                )

            self.sm.transition(job, JobState.PATCHING)
            patch = await self.services.patch.patch(repo_path, analysis, exploit)

            self.sm.transition(job, JobState.VERIFYING)
            verification = await self.services.verification.verify(
                repo_path, analysis, exploit, patch
            )
            if not getattr(verification, "verified", False):
                return self.sm.fail(
                    job,
                    FailureCode.VERIFICATION_FAILED,
                    "verification gates did not all pass",
                )

            evidence = EvidenceBuilder(
                repository=job.repository,
                commit_sha=job.commit_sha,
                finding_fingerprint=job.finding_fingerprint,
                model_provider=getattr(analysis, "model_provider", "unknown"),
                model_name=getattr(analysis, "model_name", "unknown"),
            )
            evidence.add(
                kind=EvidenceKind.ANALYSIS,
                name="analysis.txt",
                content=str(analysis),
            )
            evidence.add(
                kind=EvidenceKind.EXPLOIT,
                name="exploit.txt",
                content=str(exploit),
            )
            evidence.add(
                kind=EvidenceKind.PATCH,
                name="patch.txt",
                content=str(patch),
            )
            evidence.add(
                kind=EvidenceKind.TEST,
                name="verification.txt",
                content=str(verification),
            )
            evidence_doc = evidence.build(verified=True)
            evidence_path = self.services.evidence_store.write(
                "evidence", evidence_doc
            )
            job.evidence_id = evidence_doc.evidence_id

            self.sm.transition(job, JobState.VERIFIED)

            patch_files = getattr(patch, "files", {})
            pr = await self.services.pr_publisher.publish(
                owner=owner,
                repo=repo,
                base_branch=base_branch,
                base_sha=job.commit_sha,
                patch_files=patch_files,
                evidence=evidence_doc,
                title=f"fix(security): remediate {job.finding_fingerprint}",
                branch=f"patchproof/{job.finding_fingerprint}",
            )
            job.pull_request_url = getattr(pr, "html_url", None) or pr.get("url")
            self.sm.transition(job, JobState.PR_CREATED)
            return job

        except Exception as exc:
            if job.state in {
                JobState.RECEIVED,
                JobState.ANALYZING,
                JobState.EXPLOITING,
                JobState.PATCHING,
                JobState.VERIFYING,
            }:
                return self.sm.fail(
                    job, FailureCode.INTERNAL_ERROR, f"{type(exc).__name__}: {exc}"
                )
            raise
