from __future__ import annotations
from dataclasses import dataclass


@dataclass
class PipelineAdapters:
    clone: object
    scan: object
    analyze: object
    patch: object
    verify: object
    evidence: object
    github: object


class VerifiedGitHubPublisher:
    """Guardrail: publication is impossible unless verification says true."""

    def __init__(self, github_client):
        self.client = github_client

    def publish_verified(self, *, repository, commit_sha, patch_result, evidence):
        if not evidence.get("verified", False):
            raise PermissionError("refusing to publish unverified remediation")
        owner, repo = repository.split("/", 1)
        head = patch_result["head_branch"]
        base = patch_result.get("base_branch", "main")
        title = patch_result.get("title", "PatchProof: verified security remediation")
        body = (
            "PatchProof automatically generated and verified this remediation.\n\n"
            f"Verification evidence: {evidence.get('evidence_id', 'attached')}"
        )
        return self.client.create_pull_request(owner, repo, title, head, base, body)
