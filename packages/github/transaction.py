from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class PublicationPhase(str, Enum):
    READY = "ready"
    BRANCH_PUSHED = "branch_pushed"
    PR_CREATED = "pr_created"


class PublicationTransactionError(RuntimeError):
    pass


@dataclass(frozen=True)
class PublicationRecord:
    job_id: str
    evidence_sha256: str
    branch: str
    commit_sha: str
    phase: PublicationPhase
    pr_number: int | None = None
    pr_url: str | None = None


class PublicationTransaction:
    def __init__(self, record_store, git_publisher, github_publisher):
        self.record_store = record_store
        self.git_publisher = git_publisher
        self.github_publisher = github_publisher

    def publish(self, *, job, evidence, patch_diff, title, body, head, base):
        existing = self.record_store.get(job.job_id)

        if existing and existing.evidence_sha256 != evidence.evidence_sha256:
            raise PublicationTransactionError(
                "job already has a publication transaction for different evidence"
            )

        if existing and existing.phase == PublicationPhase.PR_CREATED:
            return existing

        if existing and existing.phase == PublicationPhase.BRANCH_PUSHED:
            commit_sha = existing.commit_sha
        else:
            commit_sha = self.git_publisher.create_and_push(
                head, base, patch_diff
            )
            self.record_store.put(PublicationRecord(
                job_id=job.job_id,
                evidence_sha256=evidence.evidence_sha256,
                branch=head,
                commit_sha=commit_sha,
                phase=PublicationPhase.BRANCH_PUSHED,
            ))

        pr = self.github_publisher.publish(
            job=job, evidence=evidence, title=title, body=body,
            head=head, base=base,
        )

        record = PublicationRecord(
            job_id=job.job_id,
            evidence_sha256=evidence.evidence_sha256,
            branch=head,
            commit_sha=commit_sha,
            phase=PublicationPhase.PR_CREATED,
            pr_number=pr["number"],
            pr_url=pr["url"],
        )
        self.record_store.put(record)
        return record
