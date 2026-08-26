from __future__ import annotations
from dataclasses import dataclass


class PublicationRejected(RuntimeError):
    pass

PublicationDenied = PublicationRejected


@dataclass(frozen=True)
class VerificationEvidence:
    verified: bool
    commit_sha: str
    patch_sha256: str
    test_summary: str
    scanner_summary: str

    def validate(self, expected_commit_sha: str) -> None:
        if self.commit_sha != expected_commit_sha:
            raise PublicationRejected("verification evidence commit does not match job commit")

@dataclass(frozen=True)
class PullRequest:
    number: int
    url: str
    head_sha: str

    @property
    def html_url(self) -> str:
        return self.url


class GitHubPublisher:
    def __init__(self, client, state_store=None, installation_id=None):
        self.client = client
        self.state_store = state_store
        self.installation_id = installation_id

    def publish_verified(self, *, job, patch_result, evidence):
        state = self.state_store.state(job.job_id) if self.state_store else None
        value = getattr(state, "value", state)
        if value != "verified":
            raise PublicationRejected(f"publication requires VERIFIED state, got {value}")
        if not getattr(evidence, "verified", True):
            raise PublicationRejected("verification evidence is not verified")
        if getattr(evidence, "commit_sha", None) != job.commit_sha:
            raise PublicationRejected("verification evidence commit does not match job commit")

        import hashlib
        digest = hashlib.sha256(patch_result.diff.encode()).hexdigest()
        if getattr(evidence, "patch_sha256", None) != digest:
            raise PublicationRejected("verification evidence patch digest does not match patch")

        body = (
            f"{getattr(patch_result, 'title', 'PatchProof security fix')}\\n\\n"
            f"{getattr(evidence, 'test_summary', '')}\\n"
            f"{getattr(evidence, 'scanner_summary', '')}\\n"
            f"Patch SHA-256: {digest}"
        )
        if hasattr(self.client, "create_pull_request"):
            idempotency_key = f"patchproof:{job.job_id}:{digest}"
            result = self.client.create_pull_request(
                installation_id=self.installation_id,
                repository=job.repository,
                head=patch_result.branch,
                base=patch_result.base_branch,
                title=patch_result.title,
                body=body,
                idempotency_key=idempotency_key,
            )
            if isinstance(result, dict):
                return {
                    "number": result["number"],
                    **({"url": result["url"]} if "url" in result else {}),
                }
            return {
                "number": result.number,
                **({"url": result.url} if getattr(result, "url", None) else {}),
            }
        raise PublicationRejected("GitHub client cannot create pull requests")

    def publish(self, *, job=None, evidence=None, title, body=None, head=None, base=None,
                owner=None, repo=None, base_branch=None, base_sha=None, patch_files=None,
                branch=None):
        if job is None:
            head = head or branch
            base = base or base_branch
            body = body or ""
        else:
            head = head or getattr(job, "head", None)
            base = base or base_branch
        if evidence is None:
            raise PublicationRejected("publication requires persisted evidence")
        evidence_sha = getattr(evidence, "evidence_sha256",
                                getattr(evidence, "manifest_sha256", None))
        if not evidence_sha:
            raise PublicationRejected("publication evidence has no digest")

        existing = self.client.find_pull_request(
            head=head,
            base=base,
            evidence_sha256=evidence_sha,
        )
        if existing:
            return {
                "number": existing["number"],
                "url": existing["url"],
                "head_sha": existing.get("head_sha", head),
            }

        result = self.client.create_pull_request(
            title=title,
            body=body or "",
            head=head,
            base=base,
            evidence_sha256=evidence_sha,
        )
        return {
            "number": result["number"],
            "url": result["url"],
            "head_sha": result.get("head_sha", head),
        }

class VerifiedPublicationService:
    def __init__(self, state_machine, evidence_store, publisher):
        self.state_machine = state_machine
        self.evidence_store = evidence_store
        self.publisher = publisher

    def publish(self, *, job, title, body, head, base):
        state = self.state_machine.state(job.job_id)
        value = state.value if hasattr(state, "value") else str(state)

        evidence = self.evidence_store.get(job.job_id)
        if value == "pr_created" and evidence is not None:
            existing = self.publisher.client.find_pull_request(
                head=head,
                base=base,
                evidence_sha256=getattr(
                    evidence, "evidence_sha256",
                    getattr(evidence, "manifest_sha256", None),
                ),
            )
            if existing:
                return {
                    "number": existing["number"],
                    "url": existing["url"],
                    "head_sha": existing.get("head_sha", head),
                }

        if value != "verified":
            raise PublicationRejected(
                f"GitHub publication requires VERIFIED state, got {state}"
            )

        if evidence is None:
            raise PublicationRejected("VERIFIED job has no persisted evidence")

        pr = self.publisher.publish(
            job=job,
            evidence=evidence,
            title=title,
            body=body,
            head=head,
            base=base,
        )
        self.state_machine.mark_pr_created(job.job_id)
        return pr
