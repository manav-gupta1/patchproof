from __future__ import annotations

from packages.github.publisher import PublicationDenied, VerificationEvidence
from packages.jobs.state import JobState


class VerifiedPublicationService:
    def __init__(self, state_store, github_client, installation_id):
        self.state_store = state_store
        self.github_client = github_client
        self.installation_id = installation_id

    def publish(self, *, job, patch_result, evidence: VerificationEvidence):
        evidence.validate(job.commit_sha)

        state = self.state_store.state(job.job_id)
        if state != JobState.VERIFIED:
            raise PublicationDenied("publication requires durable verified state")

        marker = (
            f"patchproof:{job.job_id}:"
            f"{evidence.commit_sha}:{evidence.patch_sha256}"
        )

        pr = self.github_client.create_pull_request(
            installation_id=self.installation_id,
            repository=job.repository,
            head=patch_result.branch,
            base=patch_result.base_branch,
            title=patch_result.title,
            body=(
                "## PatchProof verification\n\n"
                f"<!-- {marker} -->\n"
                f"- Target commit: `{evidence.commit_sha}`\n"
                f"- Patch SHA-256: `{evidence.patch_sha256}`\n"
                f"- Tests: {evidence.test_summary}\n"
                f"- Scanner: {evidence.scanner_summary}\n"
            ),
            idempotency_key=marker,
        )

        return pr
