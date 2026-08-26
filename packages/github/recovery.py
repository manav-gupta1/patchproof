from __future__ import annotations

from packages.github.transaction import PublicationPhase


class PublicationRecoveryWorker:
    def __init__(self, record_store, publisher):
        self.record_store = record_store
        self.publisher = publisher

    def recover(self, *, job, evidence, title, body, head, base):
        record = self.record_store.get(job.job_id)
        if record is None:
            return None
        if record.evidence_sha256 != evidence.evidence_sha256:
            raise RuntimeError("recovery evidence does not match durable record")
        if record.phase == PublicationPhase.PR_CREATED:
            return record
        if record.phase != PublicationPhase.BRANCH_PUSHED:
            raise RuntimeError(f"unsupported recovery phase: {record.phase}")

        pr = self.publisher.publish(
            job=job,
            evidence=evidence,
            title=title,
            body=body,
            head=head,
            base=base,
        )
        from packages.github.transaction import PublicationRecord
        completed = PublicationRecord(
            job_id=record.job_id,
            evidence_sha256=record.evidence_sha256,
            branch=record.branch,
            commit_sha=record.commit_sha,
            phase=PublicationPhase.PR_CREATED,
            pr_number=pr["number"],
            pr_url=pr["url"],
        )
        self.record_store.put(completed)
        return completed
