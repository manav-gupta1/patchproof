from __future__ import annotations

from packages.state import Job, JobState, JobStateMachine
from packages.state.evidence import make_evidence


class RemediationOrchestrator:
    def __init__(self, job: Job):
        self.job = job
        self.sm = JobStateMachine(job)

    def record(self, kind: str, payload: dict, *, actor: str, reason: str):
        evidence = make_evidence(kind, payload)
        self.job.add_evidence(evidence)
        return evidence

    def complete(self, state: JobState, *, actor: str, reason: str, evidence_kind: str, evidence: dict):
        record = self.record(evidence_kind, evidence, actor=actor, reason=reason)
        self.sm.transition(state, actor=actor, reason=reason)
        return record
