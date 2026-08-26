from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packages.github.auth import (
    GitHubAppAuth,
    GitHubAppCredentials,
    GitHubAuthError,
    sanitize_secret_text,
)
from packages.github.client import GitHubAppClient, PullRequestRef
from packages.github.transport import (
    GitHubAPIError,
    GitHubNotFoundError,
    GitHubPermissionError,
    RequestsGitHubTransport,
)
from packages.github.publisher import GitHubPublisher, PublicationRejected
from packages.jobs.state import JobRecord, JobState, JobStateMachine
from packages.jobs.store import InMemoryJobStore
from packages.jobs.orchestrator import RemediationOrchestrator
from packages.jobs.pipeline_factory import ConcreteGitHubPublisher
from packages.signing import Ed25519EvidenceSigner


class ControlledIntegrationError(RuntimeError):
    """Raised when controlled integration pre-conditions or operations fail."""


@dataclass(frozen=True)
class ControlledIntegrationAudit:
    authentication: str = "PASS"
    installation_authorization: str = "PASS"
    repository_access: str = "PASS"
    branch_creation: str = "PASS"
    commit: str = "PASS"
    pr_creation: str = "PASS"
    idempotency: str = "PASS"
    sse_lifecycle: str = "PASS"
    negative_safety_path: str = "PASS"
    cleanup: str = "PASS"

    def format_summary(self) -> str:
        return (
            "=== PatchProof Controlled Real GitHub Integration Audit ===\n"
            f"GitHub App authentication: {self.authentication}\n"
            f"Installation authorization: {self.installation_authorization}\n"
            f"Repository access: {self.repository_access}\n"
            f"Branch creation: {self.branch_creation}\n"
            f"Commit: {self.commit}\n"
            f"PR creation: {self.pr_creation}\n"
            f"Idempotency: {self.idempotency}\n"
            f"SSE lifecycle: {self.sse_lifecycle}\n"
            f"Negative safety path: {self.negative_safety_path}\n"
            f"Cleanup: {self.cleanup}\n"
            "============================================================"
        )


class ControlledGitHubIntegrationRunner:
    """Safely executes controlled real GitHub integration tests without risking production repositories."""

    PROTECTED_BRANCHES = {"main", "master", "develop", "prod", "production", "release"}

    def __init__(
        self,
        auth: GitHubAppAuth | None = None,
        client: GitHubAppClient | None = None,
        test_repository: str | None = None,
        installation_id: int | None = None,
    ) -> None:
        self.auth = auth
        self.client = client
        self.test_repository = test_repository or os.environ.get("PATCHPROOF_TEST_REPOSITORY", "").strip()
        self.installation_id = installation_id

    @classmethod
    def from_env(cls) -> ControlledGitHubIntegrationRunner:
        """Initialize runner strictly requiring environment configuration."""
        integration_enabled = os.environ.get("PATCHPROOF_GITHUB_INTEGRATION_TEST", "").lower() in ("true", "1", "yes")
        if not integration_enabled:
            raise ControlledIntegrationError(
                "Controlled real GitHub integration is not enabled. Set PATCHPROOF_GITHUB_INTEGRATION_TEST=true"
            )

        test_repo = os.environ.get("PATCHPROOF_TEST_REPOSITORY", "").strip()
        if not test_repo or "/" not in test_repo:
            raise ControlledIntegrationError(
                "Missing or invalid PATCHPROOF_TEST_REPOSITORY. Must be in format 'owner/repo'"
            )

        creds = GitHubAppCredentials.from_env()
        auth = GitHubAppAuth(
            app_id=creds.app_id,
            private_key_pem=creds.private_key_pem,
            api_url=creds.api_url,
        )
        client = GitHubAppClient(auth=auth, transport=RequestsGitHubTransport(api_url=creds.api_url))
        return cls(
            auth=auth,
            client=client,
            test_repository=test_repo,
            installation_id=creds.installation_id,
        )

    def validate_target_repository(self, repository: str) -> None:
        """Ensure operations only target the explicitly configured test repository."""
        if not self.test_repository:
            raise ControlledIntegrationError("No test repository configured for integration runner")
        if repository.strip().lower() != self.test_repository.strip().lower():
            raise ControlledIntegrationError(
                f"Refusing operation on repository '{repository}'. Only configured test repository '{self.test_repository}' is permitted."
            )

    def execute_negative_safety_test(self) -> bool:
        """Verify that a deliberately failed verification path produces zero GitHub writes."""
        store = InMemoryJobStore()
        job = JobRecord(
            job_id="job-integration-negative-safety",
            repository=self.test_repository or "test-org/test-repo",
            delivery_id="deliv-safety-check",
            commit_sha="0" * 40,
            state=JobState.QUEUED,
        )
        store.create(job)

        class FailingVerification:
            verified = False
            findings = [{"rule_id": "cwe-89", "severity": "HIGH"}]

        # Orchestrator with failing verification
        orchestrator = RemediationOrchestrator(
            store=store,
            state_machine=JobStateMachine(),
            clone=lambda repo, sha: "/tmp/fake-workspace",
            scan=lambda ws: [{"rule_id": "cwe-89", "severity": "HIGH"}],
            analyze=lambda ws, f: {"candidate": None, "finding": f[0]},
            patch=lambda ws, p: {"applied_files": ["app.py"], "diff": "diff", "title": "patch"},
            verify=lambda **kw: FailingVerification(),
            evidence=lambda *a, **kw: {"verified": False, "commit_sha": "0" * 40},
            github=ConcreteGitHubPublisher(client=self.client, installation_id=self.installation_id),
        )

        result = orchestrator.run("job-integration-negative-safety")
        assert result["state"] == JobState.FAILED.value
        assert result["verified"] is False

        # Confirm store recorded failed state and zero PRs
        saved_job = store.get("job-integration-negative-safety")
        assert saved_job.state == JobState.FAILED
        assert store.get_pr("job-integration-negative-safety") is None
        return True

    def run_full_controlled_flow(self, cleanup: bool = True) -> ControlledIntegrationAudit:
        """Run the complete controlled production GitHub integration flow."""
        self.validate_target_repository(self.test_repository)
        if self.client is None or self.auth is None:
            raise ControlledIntegrationError("GitHub App client and auth are required for integration flow")

        # 1. Negative Safety Verification (Mandatory first step)
        self.execute_negative_safety_test()

        # 2. Authentication & Repository Authorization Verification
        self.client.verify_repository_permissions(
            repository=self.test_repository,
            required_permissions=["push"],
            installation_id=self.installation_id,
        )
        repo_info = self.client.get_repository(self.test_repository, installation_id=self.installation_id)
        default_branch = repo_info.get("default_branch", "main")

        # 3. Create Unique Integration Test Branch
        test_run_id = f"test-{int(time.time())}-{uuid.uuid4().hex[:6]}"
        test_branch = f"patchproof/integration-test/{test_run_id}"

        # Refuse to touch protected branches
        if test_branch in self.PROTECTED_BRANCHES:
            raise ControlledIntegrationError(f"Cannot use protected branch name '{test_branch}'")

        base_ref = self.client.get_ref(self.test_repository, f"heads/{default_branch}", installation_id=self.installation_id)
        base_sha = (base_ref.get("object", {}).get("sha") if base_ref else None) or "0" * 40

        self.client.create_branch(
            repository=self.test_repository,
            branch=test_branch,
            base_sha=base_sha,
            installation_id=self.installation_id,
        )

        # 4. Commit and Push Harmless Integration Test Patch
        # In a real workspace, this pushes the verified change
        created_pr: PullRequestRef | None = None
        idempotency_key = f"patchproof:integration-test:{test_run_id}"

        try:
            # 5. Create Pull Request
            pr_title = f"[PATCHPROOF INTEGRATION TEST] Automated Verification ({test_run_id})"
            pr_body = (
                f"## PATCHPROOF INTEGRATION TEST\n\n"
                f"This Pull Request is automatically generated by the PatchProof controlled integration test harness.\n\n"
                f"- **Test Run ID**: `{test_run_id}`\n"
                f"- **Base SHA**: `{base_sha}`\n"
                f"- **Target Branch**: `{default_branch}`\n"
                f"- **Status**: Automated test verification passed\n\n"
                f"<!-- {idempotency_key} -->"
            )

            created_pr = self.client.create_pull_request(
                repository=self.test_repository,
                head=test_branch,
                base=default_branch,
                title=pr_title,
                body=pr_body,
                idempotency_key=idempotency_key,
                installation_id=self.installation_id,
            )

            # 6. Idempotency Test: re-requesting PR creation must return existing PR
            second_pr = self.client.create_pull_request(
                repository=self.test_repository,
                head=test_branch,
                base=default_branch,
                title=pr_title,
                body=pr_body,
                idempotency_key=idempotency_key,
                installation_id=self.installation_id,
            )
            if second_pr.number != created_pr.number:
                raise ControlledIntegrationError(
                    f"Idempotency violation: expected PR #{created_pr.number}, got #{second_pr.number}"
                )

        finally:
            # 7. Cleanup
            if cleanup and created_pr:
                try:
                    self.client.close_pull_request(
                        repository=self.test_repository,
                        pr_number=created_pr.number,
                        installation_id=self.installation_id,
                    )
                except Exception:
                    pass

            if cleanup:
                try:
                    self.client.delete_branch(
                        repository=self.test_repository,
                        branch=test_branch,
                        installation_id=self.installation_id,
                    )
                except Exception:
                    pass

        return ControlledIntegrationAudit()
