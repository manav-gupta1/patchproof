from __future__ import annotations

from packages.evidence.execution import build_authoritative_bundle


class VerificationRejected(RuntimeError):
    pass


class DurableVerificationService:
    def __init__(self, sandbox_pipeline, evidence_store, state_machine):
        self.pipeline = sandbox_pipeline
        self.evidence_store = evidence_store
        self.state_machine = state_machine

    def verify(self, *, job, patch_diff):
        # Existing state machine remains authoritative.
        current = self.state_machine.state(job.job_id)
        if str(current.value if hasattr(current, "value") else current) != "verifying":
            raise VerificationRejected(
                f"verification requires VERIFYING state, got {current}"
            )

        result = self.pipeline.run()

        if not result.verification.verified:
            self.state_machine.fail(job.job_id)
            raise VerificationRejected("sandbox verification failed")

        bundle, execution = build_authoritative_bundle(
            job_id=job.job_id,
            commit_sha=job.commit_sha,
            patch_diff=patch_diff,
            scanner=result.scanner,
            tests=result.tests,
            verification=result.verification,
        )

        # Persistence is deliberately before VERIFIED.
        self.evidence_store.put(bundle)
        self.state_machine.mark_verified(job.job_id)

        return bundle, execution
