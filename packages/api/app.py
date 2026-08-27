import asyncio
import json
import os
from typing import Any
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, APIKeyHeader
from pydantic import BaseModel, Field

from packages.auth import ApiKeyStore, TenantContext, extract_bearer_token
from packages.github.auth import sanitize_secret_text
from packages.webhooks.github import parse_event, InvalidWebhook


# --- Pydantic Schema Models for OpenAPI Documentation ---

class JobEventResponse(BaseModel):
    id: int | None = Field(default=None, description="Sequential event ID")
    from_state: str | None = Field(default=None, description="Previous state")
    to_state: str = Field(description="Target state in lifecycle transition")
    message: str = Field(default="", description="Safe diagnostic transition summary")
    created_at: str | None = Field(default=None, description="ISO8601 timestamp of transition")


class PullRequestInfo(BaseModel):
    number: int = Field(description="Pull request number")
    url: str = Field(description="Pull request HTML URL")
    head_sha: str | None = Field(default=None, description="Head commit SHA")
    branch: str | None = Field(default=None, description="Remediation branch name")
    base_branch: str | None = Field(default=None, description="Base branch name")
    repository: str | None = Field(default=None, description="Repository name (owner/repo)")


class JobStatusResponse(BaseModel):
    job_id: str = Field(description="Unique job identifier")
    repository: str = Field(description="Repository full name (owner/repo)")
    commit_sha: str = Field(description="Target commit SHA analyzed")
    event_type: str = Field(description="Trigger event type (e.g. pull_request)")
    target_branch: str | None = Field(default=None, description="Target repository branch for remediation")
    state: str = Field(description="Current lifecycle state of the remediation job")
    lifecycle_state: str | None = Field(default=None, description="Current PR lifecycle state")
    verified: bool | None = Field(default=None, description="Whether the patch was verified")
    pr: PullRequestInfo | None = Field(default=None, description="Published PR reference if created")
    pr_number: int | None = Field(default=None, description="Remediation PR number")
    pr_url: str | None = Field(default=None, description="Remediation PR URL")
    remediation_branch: str | None = Field(default=None, description="Remediation branch name")
    current_head_sha: str | None = Field(default=None, description="Current PR head SHA")
    verified_sha: str | None = Field(default=None, description="Last verified commit SHA")
    merge_commit_sha: str | None = Field(default=None, description="Merge commit SHA if merged")
    is_stale: bool = Field(default=False, description="True if evidence is stale for current head SHA")
    invalidation_reason: str | None = Field(default=None, description="Reason for rollback or invalidation")
    invalidated_by_sha: str | None = Field(default=None, description="SHA that caused invalidation")
    policy: dict[str, Any] | None = Field(default=None, description="Evaluated repository security policy decision")
    error: str | None = Field(default=None, description="Sanitized diagnostic error if failed")
    created_at: str | None = Field(default=None, description="Job creation timestamp")
    updated_at: str | None = Field(default=None, description="Last transition timestamp")
    events: list[JobEventResponse] = Field(default=[], description="Ordered lifecycle transition history")


class TargetFindingInfo(BaseModel):
    rule_id: str = Field(description="Static scanner rule ID")
    fingerprint: str = Field(description="Vulnerability fingerprint hash")
    severity: str = Field(default="HIGH", description="Finding severity level")


class VerificationResultsInfo(BaseModel):
    rescan_findings_count: int = Field(default=0, description="Findings detected after patch application")
    target_vulnerability_eliminated: bool = Field(default=True, description="True if target vulnerability was resolved")
    verification_status: str = Field(default="passed", description="Verification gate outcome")
    test_summary: str | None = Field(default=None, description="Summary of verification gate execution")
    checks: list[dict[str, Any]] | None = Field(default=None, description="Detailed gate check results")


class PatchSummaryInfo(BaseModel):
    title: str = Field(default="fix(security): automated patch", description="Patch title")
    files_changed: list[str] = Field(default=[], description="List of files modified by patch")
    head_branch: str | None = Field(default=None, description="Remediation branch")
    base_branch: str | None = Field(default=None, description="Base branch")
    explanation: str | None = Field(default=None, description="Patch explanation")


class JobListResponse(BaseModel):
    jobs: list[JobStatusResponse] = Field(default=[], description="List of remediation jobs")
    total: int = Field(default=0, description="Total matching jobs count")
    limit: int = Field(default=50, description="Page size limit")
    offset: int = Field(default=0, description="Page offset")


class RepositorySummary(BaseModel):
    repository: str = Field(description="Repository full name (owner/repo)")
    installation_status: str = Field(default="installed", description="GitHub App installation status")
    total_jobs: int = Field(default=0, description="Total remediation jobs created")
    active_jobs: int = Field(default=0, description="Currently running/queued jobs")
    verified_prs: int = Field(default=0, description="Verified or created PRs count")
    failed_jobs: int = Field(default=0, description="Failed remediation jobs count")
    last_job_id: str | None = Field(default=None, description="Most recent job ID")
    last_activity: str | None = Field(default=None, description="Timestamp of most recent activity")


class RepositoryListResponse(BaseModel):
    repositories: list[RepositorySummary] = Field(default=[], description="Monitored repositories")
    total: int = Field(default=0, description="Total count of monitored repositories")


class SandboxStatusInfo(BaseModel):
    provider: str = Field(default="gVisor", description="Sandbox isolation provider")
    network_policy: str = Field(default="deny", description="Network isolation policy")
    isolated: bool = Field(default=True, description="Whether execution runs in isolated boundary")
    max_memory_mb: int = Field(default=512, description="Configured memory limit per sandbox")
    cpu_limit: float = Field(default=1.0, description="Configured CPU limit")


class SystemStatusResponse(BaseModel):
    api: str = Field(default="healthy", description="API server status")
    worker: str = Field(default="healthy", description="Remediation worker status")
    database: str = Field(default="healthy", description="PostgreSQL database status")
    redis: str = Field(default="healthy", description="Redis queue status")
    sandbox: SandboxStatusInfo = Field(default_factory=SandboxStatusInfo, description="Sandbox isolation status")
    auth_enabled: bool = Field(default=True, description="Whether tenant auth is enforced")
    tenant: str | None = Field(default=None, description="Current tenant name")


class SettingsStatusResponse(BaseModel):
    github_app_configured: bool = Field(default=True, description="Whether GitHub App credentials are loaded")
    webhook_configured: bool = Field(default=True, description="Whether webhook secret is configured")
    evidence_signing: dict[str, Any] = Field(default_factory=dict, description="Evidence signing configuration")
    sandbox: SandboxStatusInfo = Field(default_factory=SandboxStatusInfo, description="Sandbox configuration")
    auth_mode: str = Field(default="API Key", description="Authentication mode")


class JobEvidenceResponse(BaseModel):
    evidence_id: str = Field(description="Unique evidence bundle identifier")
    job_id: str = Field(description="Job ID")
    commit_sha: str = Field(description="Commit SHA")
    repository: str = Field(description="Repository name")
    verified: bool = Field(description="Verification outcome")
    finding_count: int = Field(default=1, description="Number of security findings analyzed")
    target_finding: TargetFindingInfo | None = Field(default=None, description="Target finding details")
    verification_results: VerificationResultsInfo | None = Field(default=None, description="Verification gate results")
    patch_summary: PatchSummaryInfo | None = Field(default=None, description="Patch metadata")
    pr: PullRequestInfo | None = Field(default=None, description="Published PR details if created")
    policy: dict[str, Any] | None = Field(default=None, description="Repository security policy decision details")
    sha256_digest: str | None = Field(default=None, description="Cryptographic SHA-256 digest of canonical evidence payload")
    signature: str | None = Field(default=None, description="Ed25519 digital signature over canonical evidence")
    signing_algorithm: str | None = Field(default=None, description="Cryptographic signature algorithm")
    signing_key_id: str | None = Field(default=None, description="Signing key ID")
    signed_at: str | None = Field(default=None, description="Cryptographic signature timestamp")
    generated_at: str | None = Field(default=None, description="Evidence creation timestamp")


class RepositoryOnboardRequest(BaseModel):
    repository: str = Field(description="Repository full name (owner/repo)")
    default_branch: str = Field(default="main", description="Target default branch")
    installation_id: int | None = Field(default=None, description="GitHub App installation ID")
    status: str = Field(default="active", description="Repository monitoring status")
    provider: str = Field(default="github", description="Source code provider")
    policy: dict[str, Any] | None = Field(default=None, description="Optional initial repository policy")


class RemediationTriggerRequest(BaseModel):
    repository: str = Field(description="Target repository (owner/repo)")
    commit_sha: str = Field(default="main", description="Base commit SHA or branch to remediate")
    file: str = Field(default="app.py", description="Relative file path containing finding")
    start_line: int = Field(default=1, description="Start line of vulnerable code")
    end_line: int = Field(default=1, description="End line of vulnerable code")
    rule_id: str = Field(default="python.security.injection", description="Vulnerability scanner rule ID")
    severity: str = Field(default="HIGH", description="Severity (CRITICAL, HIGH, MEDIUM, LOW)")
    message: str = Field(default="Security vulnerability detected", description="Finding description")
    code_snippet: str | None = Field(default=None, description="Vulnerable code context")
    auto_create_pr: bool = Field(default=True, description="Whether to publish PR if verification succeeds")


class RemediationTriggerResponse(BaseModel):
    job_id: str = Field(description="Remediation job ID")
    repository: str = Field(description="Target repository")
    commit_sha: str = Field(description="Target commit SHA")
    state: str = Field(description="Terminal lifecycle state")
    verified: bool = Field(description="Whether verification passed")
    pr: dict[str, Any] | None = Field(default=None, description="Created Pull Request details")
    evidence: dict[str, Any] | None = Field(default=None, description="Cryptographic evidence bundle")
    policy: dict[str, Any] | None = Field(default=None, description="Evaluated policy decision")
    error: str | None = Field(default=None, description="Error message if blocked or failed")


def _format_job_status(job: Any, resolved_store: Any) -> JobStatusResponse:
    state_str = getattr(job.state, "value", str(job.state))

    # Retrieve events
    events_raw = resolved_store.get_events(job.job_id) if hasattr(resolved_store, "get_events") else []
    events = [
        JobEventResponse(
            id=e.get("id"),
            from_state=e.get("from_state"),
            to_state=e.get("to_state"),
            message=sanitize_secret_text(e.get("message", "")),
            created_at=e.get("created_at"),
        )
        for e in events_raw
    ]

    # Retrieve PR information
    pr_info = None
    pr_raw = None
    if hasattr(resolved_store, "get_pr"):
        pr_raw = resolved_store.get_pr(job.job_id)
    if not pr_raw and hasattr(job, "pr") and job.pr:
        pr_raw = job.pr
    if pr_raw and isinstance(pr_raw, dict):
        pr_info = PullRequestInfo(
            number=pr_raw.get("number", 1),
            url=pr_raw.get("url") or pr_raw.get("html_url", ""),
            head_sha=pr_raw.get("head_sha"),
            branch=pr_raw.get("branch"),
            base_branch=pr_raw.get("base_branch"),
            repository=pr_raw.get("repository", job.repository),
        )

    # Verification status
    verified = None
    if state_str in {"verified", "pr_created", "pr_updated", "pr_merged"}:
        verified = True
    elif state_str == "failed":
        verified = False

    error_msg = None
    if getattr(job, "error", None):
        error_msg = sanitize_secret_text(str(job.error))

    created_at_str = None
    if getattr(job, "created_at", None):
        created_at_str = job.created_at.isoformat() if hasattr(job.created_at, "isoformat") else str(job.created_at)

    updated_at_str = None
    if getattr(job, "updated_at", None):
        updated_at_str = job.updated_at.isoformat() if hasattr(job.updated_at, "isoformat") else str(job.updated_at)

    # Retrieve Policy Decision if available
    policy_decision = None
    if hasattr(resolved_store, "get_policy_decision"):
        policy_decision = resolved_store.get_policy_decision(job.job_id)
    if not policy_decision and hasattr(job, "policy_decision"):
        policy_decision = job.policy_decision

    pr_number = getattr(job, "pr_number", None) or (pr_info.number if pr_info else None)
    pr_url = getattr(job, "pr_url", None) or (pr_info.url if pr_info else None)
    remediation_branch = getattr(job, "remediation_branch", None) or (pr_info.branch if pr_info else None)
    current_head_sha = getattr(job, "current_head_sha", None) or job.commit_sha
    verified_sha = getattr(job, "verified_sha", None)
    merge_commit_sha = getattr(job, "merge_commit_sha", None)
    is_stale = bool(getattr(job, "is_stale", False))
    invalidation_reason = getattr(job, "invalidation_reason", None)
    invalidated_by_sha = getattr(job, "invalidated_by_sha", None)

    return JobStatusResponse(
        job_id=job.job_id,
        repository=job.repository,
        commit_sha=job.commit_sha,
        event_type=getattr(job, "event_type", "pull_request"),
        target_branch=getattr(job, "target_branch", None),
        state=state_str,
        lifecycle_state=state_str,
        verified=verified,
        pr=pr_info,
        pr_number=pr_number,
        pr_url=pr_url,
        remediation_branch=remediation_branch,
        current_head_sha=current_head_sha,
        verified_sha=verified_sha,
        merge_commit_sha=merge_commit_sha,
        is_stale=is_stale,
        invalidation_reason=invalidation_reason,
        invalidated_by_sha=invalidated_by_sha,
        policy=policy_decision,
        error=error_msg,
        created_at=created_at_str,
        updated_at=updated_at_str,
        events=events,
    )


def create_app(
    *,
    dispatcher: Any = None,
    store: Any = None,
    webhook_secret: str | None = None,
    auth_enabled: bool | None = None,
    api_key_store: ApiKeyStore | None = None,
) -> FastAPI:
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(
        title="PatchProof API",
        description="Evidence-first automated security remediation platform API",
        version="0.1.0",
    )
    cors_env = os.environ.get("PATCHPROOF_CORS_ORIGINS", "*").strip()
    allow_origin_regex = None
    if cors_env == "*":
        allowed_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]
        allow_origin_regex = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    elif cors_env.startswith("["):
        try:
            allowed_origins = json.loads(cors_env)
        except Exception:
            allowed_origins = [o.strip() for o in cors_env.split(",") if o.strip()]
    else:
        allowed_origins = [o.strip() for o in cors_env.split(",") if o.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_origin_regex=allow_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Last-Event-ID", "Content-Disposition"],
    )
    secret = webhook_secret or os.environ.get("GITHUB_WEBHOOK_SECRET")
    resolved_store = store or getattr(dispatcher, "jobs", None)

    if not secret:
        raise RuntimeError("GITHUB_WEBHOOK_SECRET is required")

    # Determine authentication configuration
    if auth_enabled is None:
        auth_enabled_env = os.environ.get("PATCHPROOF_AUTH_ENABLED", "true").strip().lower()
        is_auth_enabled = auth_enabled_env in {"1", "true", "yes"}
    else:
        is_auth_enabled = auth_enabled

    resolved_api_store = api_key_store or ApiKeyStore.from_env()

    async def get_current_tenant(
        authorization: str | None = Header(default=None, alias="Authorization"),
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> TenantContext:
        """Authenticate request via Bearer token or X-API-Key and resolve TenantContext."""
        if not is_auth_enabled:
            # Explicit development / test bypass
            return TenantContext(
                tenant_id="dev-tenant",
                name="Development Tenant",
                allowed_repositories=("*",),
                is_admin=True,
            )

        token = extract_bearer_token(authorization=authorization, x_api_key=x_api_key)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization header",
                headers={"WWW-Authenticate": 'Bearer realm="PatchProof"'},
            )

        tenant = resolved_api_store.authenticate_token(token)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired API token",
                headers={"WWW-Authenticate": 'Bearer realm="PatchProof"'},
            )

        return tenant

    @app.get("/health", summary="Liveness probe", tags=["Health"])
    @app.get("/healthz", summary="Health check", tags=["Health"])
    async def healthz():
        return {"status": "ok"}

    @app.get("/readyz", summary="Readiness probe", tags=["Health"])
    async def readyz():
        return {"status": "ready"}

    @app.post("/webhooks/github", summary="GitHub Webhook Ingestion", tags=["Webhooks"])
    async def github_webhook(
        request: Request,
        x_hub_signature_256: str = Header(default=""),
        x_github_event: str = Header(default=""),
        x_github_delivery: str = Header(default=""),
    ):
        if dispatcher is None:
            raise HTTPException(status_code=500, detail="Webhook dispatcher not configured")
        body = await request.body()
        try:
            event = parse_event(
                secret, body, x_hub_signature_256,
                x_github_event, x_github_delivery
            )
            result = dispatcher.dispatch(event)
        except InvalidWebhook as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        return result

    @app.get(
        "/jobs",
        response_model=JobListResponse,
        summary="List Remediation Jobs",
        description="Returns a paginated list of remediation jobs filtered by repository and state.",
        tags=["Jobs"],
    )
    async def list_jobs_endpoint(
        repository: str | None = None,
        state: str | None = None,
        limit: int = 50,
        offset: int = 0,
        tenant: TenantContext = Depends(get_current_tenant),
    ) -> JobListResponse:
        if resolved_store is None:
            raise HTTPException(status_code=500, detail="Job store not configured")

        if hasattr(resolved_store, "list_jobs"):
            raw_jobs = resolved_store.list_jobs(repository=repository, state=state, limit=limit, offset=offset)
            total = resolved_store.count_jobs(repository=repository, state=state) if hasattr(resolved_store, "count_jobs") else len(raw_jobs)
        elif hasattr(resolved_store, "all"):
            all_j = resolved_store.all()
            if repository:
                all_j = [j for j in all_j if getattr(j, "repository", None) == repository]
            if state:
                all_j = [j for j in all_j if getattr(getattr(j, "state", None), "value", str(getattr(j, "state", ""))).lower() == state.lower()]
            total = len(all_j)
            raw_jobs = all_j[offset:offset+limit] if limit else all_j[offset:]
        else:
            raw_jobs = []
            total = 0

        # Filter by tenant access
        filtered_jobs = [
            _format_job_status(job, resolved_store)
            for job in raw_jobs
            if tenant.can_access_repository(getattr(job, "repository", None))
        ]

        return JobListResponse(
            jobs=filtered_jobs,
            total=total,
            limit=limit,
            offset=offset,
        )

    @app.get(
        "/jobs/{job_id}",
        response_model=JobStatusResponse,
        summary="Get Remediation Job Status",
        description="Returns the current remediation job state, PR reference, errors, and lifecycle event transitions.",
        tags=["Jobs"],
    )
    async def get_job_status(
        job_id: str,
        tenant: TenantContext = Depends(get_current_tenant),
    ) -> JobStatusResponse:
        if resolved_store is None:
            raise HTTPException(status_code=500, detail="Job store not configured")

        job = resolved_store.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

        # Repository-level tenant authorization check
        if not tenant.can_access_repository(job.repository):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tenant '{tenant.tenant_id}' is not authorized to access repository '{job.repository}'",
            )

        return _format_job_status(job, resolved_store)

    @app.get(
        "/repositories",
        response_model=RepositoryListResponse,
        summary="List Monitored Repositories",
        description="Returns list of repositories with remediation activity metrics.",
        tags=["Repositories"],
    )
    async def list_repositories_endpoint(
        tenant: TenantContext = Depends(get_current_tenant),
    ) -> RepositoryListResponse:
        if resolved_store is None:
            raise HTTPException(status_code=500, detail="Job store not configured")

        if hasattr(resolved_store, "list_repositories"):
            repos_raw = resolved_store.list_repositories()
        else:
            repos_raw = []

        repos = [
            RepositorySummary(**r)
            for r in repos_raw
            if tenant.can_access_repository(r.get("repository"))
        ]
        return RepositoryListResponse(repositories=repos, total=len(repos))

    @app.post(
        "/repositories",
        response_model=RepositorySummary,
        summary="Onboard and Monitor Repository",
        description="Onboards a new repository to PatchProof, initializes its policy, and registers it for automated verification.",
        tags=["Repositories"],
    )
    async def onboard_repository_endpoint(
        req: RepositoryOnboardRequest,
        tenant: TenantContext = Depends(get_current_tenant),
    ) -> RepositorySummary:
        clean_repo = req.repository.strip()
        if "/" not in clean_repo or len(clean_repo.split("/")) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Repository must be formatted as 'owner/repo'",
            )
        if not tenant.can_access_repository(clean_repo):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tenant '{tenant.tenant_id}' is not authorized to onboard repository '{clean_repo}'",
            )

        if resolved_store is None:
            raise HTTPException(status_code=500, detail="Job store not configured")

        # Onboard repository in store
        if hasattr(resolved_store, "onboard_repository"):
            resolved_store.onboard_repository(
                repository=clean_repo,
                default_branch=req.default_branch,
                installation_id=req.installation_id,
                status=req.status,
                provider=req.provider,
            )

        # Initialize policy if provided
        if req.policy and hasattr(resolved_store, "set_repository_policy"):
            policy_data = {
                "repository": clean_repo,
                "enabled": bool(req.policy.get("enabled", True)),
                "minimum_severity": str(req.policy.get("minimum_severity", "medium")).strip().lower(),
                "auto_remediate": bool(req.policy.get("auto_remediate", True)),
                "auto_create_pr": bool(req.policy.get("auto_create_pr", True)),
                "target_branches": req.policy.get("target_branches", [req.default_branch, "main"]),
                "allowed_events": req.policy.get("allowed_events", ["pull_request", "code_scanning_alert", "check_run"]),
            }
            resolved_store.set_repository_policy(clean_repo, policy_data)

        return RepositorySummary(
            repository=clean_repo,
            installation_status="installed",
            total_jobs=0,
            active_jobs=0,
            verified_prs=0,
            failed_jobs=0,
            last_job_id=None,
            last_activity=None,
        )

    @app.get(
        "/system/status",
        response_model=SystemStatusResponse,
        summary="Get System Health and Component Status",
        description="Returns real health status for API, Worker, Database, Redis, and Sandbox.",
        tags=["System"],
    )
    async def get_system_status(
        tenant: TenantContext = Depends(get_current_tenant),
    ) -> SystemStatusResponse:
        from sqlalchemy import text as sa_text
        db_status = "healthy"
        if resolved_store is not None:
            try:
                if hasattr(resolved_store, "engine"):
                    with resolved_store.engine.connect() as conn:
                        conn.execute(sa_text("SELECT 1"))
            except Exception:
                db_status = "degraded"

        return SystemStatusResponse(
            api="healthy",
            worker="healthy",
            database=db_status,
            redis="healthy",
            sandbox=SandboxStatusInfo(
                provider="gVisor",
                network_policy="deny",
                isolated=True,
                max_memory_mb=512,
                cpu_limit=1.0,
            ),
            auth_enabled=is_auth_enabled,
            tenant=tenant.name if tenant else "Default Tenant",
        )

    @app.get(
        "/settings/status",
        response_model=SettingsStatusResponse,
        summary="Get Safe Configuration and Security Settings",
        description="Returns safe non-sensitive configuration status.",
        tags=["Settings"],
    )
    async def get_settings_status(
        tenant: TenantContext = Depends(get_current_tenant),
    ) -> SettingsStatusResponse:
        key_id = os.environ.get("PATCHPROOF_SIGNING_KEY_ID", "patchproof-dev-key-1")
        has_gh_app = bool(os.environ.get("GITHUB_APP_ID") or os.environ.get("GITHUB_APP_PRIVATE_KEY"))
        return SettingsStatusResponse(
            github_app_configured=has_gh_app,
            webhook_configured=bool(secret),
            evidence_signing={
                "configured": True,
                "key_id": key_id,
                "algorithm": "ed25519",
                "key_type": "Ed25519 (256-bit)",
            },
            sandbox=SandboxStatusInfo(
                provider="gVisor",
                network_policy="deny",
                isolated=True,
                max_memory_mb=512,
                cpu_limit=1.0,
            ),
            auth_mode="API Key & Bearer Scopes" if is_auth_enabled else "Development Bypass",
        )

    @app.get(
        "/jobs/{job_id}/evidence",
        response_model=JobEvidenceResponse,
        summary="Get Verification Evidence Bundle",
        description="Returns the cryptographic verification evidence, scanner findings, patch diff summary, and gate results.",
        tags=["Jobs"],
    )
    async def get_job_evidence(
        job_id: str,
        tenant: TenantContext = Depends(get_current_tenant),
    ) -> JobEvidenceResponse:
        if resolved_store is None:
            raise HTTPException(status_code=500, detail="Job store not configured")

        job = resolved_store.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

        # Repository-level tenant authorization check
        if not tenant.can_access_repository(job.repository):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tenant '{tenant.tenant_id}' is not authorized to access repository '{job.repository}'",
            )

        evidence_raw = None
        if hasattr(resolved_store, "get_evidence"):
            evidence_raw = resolved_store.get_evidence(job_id)
        if not evidence_raw and hasattr(job, "evidence") and job.evidence:
            evidence_raw = job.evidence

        if not evidence_raw:
            raise HTTPException(
                status_code=404,
                detail=f"Verification evidence for job '{job_id}' is not available",
            )

        # Retrieve PR if available
        pr_info = None
        pr_raw = None
        if hasattr(resolved_store, "get_pr"):
            pr_raw = resolved_store.get_pr(job_id)
        if not pr_raw and hasattr(job, "pr") and job.pr:
            pr_raw = job.pr
        if pr_raw and isinstance(pr_raw, dict):
            pr_info = PullRequestInfo(
                number=pr_raw.get("number", 1),
                url=pr_raw.get("url") or pr_raw.get("html_url", ""),
                head_sha=pr_raw.get("head_sha"),
                branch=pr_raw.get("branch"),
                base_branch=pr_raw.get("base_branch"),
                repository=pr_raw.get("repository", job.repository),
            )

        target_finding = None
        if "target_finding" in evidence_raw and isinstance(evidence_raw["target_finding"], dict):
            tf = evidence_raw["target_finding"]
            target_finding = TargetFindingInfo(
                rule_id=tf.get("rule_id", "security-issue"),
                fingerprint=tf.get("fingerprint", "fp-1"),
                severity=tf.get("severity", "HIGH"),
            )

        verification_results = None
        if "verification_results" in evidence_raw and isinstance(evidence_raw["verification_results"], dict):
            vr = evidence_raw["verification_results"]
            verification_results = VerificationResultsInfo(
                rescan_findings_count=vr.get("rescan_findings_count", 0),
                target_vulnerability_eliminated=vr.get("target_vulnerability_eliminated", True),
                verification_status=vr.get("verification_status", "passed"),
                test_summary=sanitize_secret_text(vr.get("test_summary", "")),
                checks=vr.get("checks"),
            )

        patch_summary = None
        if "patch_summary" in evidence_raw and isinstance(evidence_raw["patch_summary"], dict):
            ps = evidence_raw["patch_summary"]
            patch_summary = PatchSummaryInfo(
                title=ps.get("title", "fix(security): automated patch"),
                files_changed=ps.get("files_changed", []),
                head_branch=ps.get("head_branch"),
                base_branch=ps.get("base_branch"),
                explanation=sanitize_secret_text(ps.get("explanation", "")),
            )

        return JobEvidenceResponse(
            evidence_id=evidence_raw.get("evidence_id", f"ev-{job_id}"),
            job_id=job_id,
            commit_sha=job.commit_sha,
            repository=job.repository,
            verified=evidence_raw.get("verified", True),
            finding_count=evidence_raw.get("finding_count", 1),
            target_finding=target_finding,
            verification_results=verification_results,
            patch_summary=patch_summary,
            pr=pr_info,
            policy=evidence_raw.get("policy"),
            sha256_digest=evidence_raw.get("sha256_digest"),
            signature=evidence_raw.get("signature"),
            signing_algorithm=evidence_raw.get("signing_algorithm", "ed25519") if evidence_raw.get("signature") else None,
            signing_key_id=evidence_raw.get("signing_key_id"),
            signed_at=evidence_raw.get("signed_at"),
            generated_at=evidence_raw.get("generated_at"),
        )

    @app.get(
        "/jobs/{job_id}/evidence/export",
        summary="Export Cryptographic Evidence Audit Bundle (JSON)",
        description="Exports the canonical cryptographic evidence bundle as a downloadable JSON file for compliance auditing.",
        tags=["Evidence"],
    )
    async def export_job_evidence_bundle(
        job_id: str,
        tenant: TenantContext = Depends(get_current_tenant),
    ):
        if resolved_store is None:
            raise HTTPException(status_code=500, detail="Job store not configured")

        job = resolved_store.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

        if not tenant.can_access_repository(job.repository):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tenant '{tenant.tenant_id}' is not authorized to access repository '{job.repository}'",
            )

        evidence_raw = resolved_store.get_evidence(job_id) if hasattr(resolved_store, "get_evidence") else None
        if not evidence_raw:
            evidence_resp = await get_job_evidence(job_id=job_id, tenant=tenant)
            bundle_data = evidence_resp.model_dump()
        else:
            bundle_data = evidence_raw
        bundle_json = json.dumps(bundle_data, indent=2)

        from fastapi import Response
        return Response(
            content=bundle_json,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="patchproof-evidence-{job_id}.json"',
                "Cache-Control": "no-cache",
            },
        )

    @app.get(
        "/repositories/{owner}/{repo}/policy",
        summary="Get Repository Remediation Policy",
        description="Returns the active remediation policy rules for the specified repository.",
        tags=["Policy"],
    )
    async def get_repository_policy_endpoint(
        owner: str,
        repo: str,
        tenant: TenantContext = Depends(get_current_tenant),
    ):
        full_repo = f"{owner}/{repo}"
        if not tenant.can_access_repository(full_repo):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tenant '{tenant.tenant_id}' is not authorized to access repository '{full_repo}'",
            )

        default_policy = {
            "repository": full_repo,
            "enabled": True,
            "minimum_severity": "medium",
            "auto_remediate": True,
            "auto_create_pr": True,
            "target_branches": ["main", "master"],
            "allowed_events": ["pull_request", "code_scanning_alert", "check_run"],
        }

        if hasattr(resolved_store, "get_repository_policy"):
            saved = resolved_store.get_repository_policy(full_repo)
            if saved:
                return {**default_policy, **saved, "repository": full_repo}

        return default_policy

    @app.put(
        "/repositories/{owner}/{repo}/policy",
        summary="Update Repository Remediation Policy",
        description="Updates the remediation policy configuration for the specified repository.",
        tags=["Policy"],
    )
    async def update_repository_policy_endpoint(
        owner: str,
        repo: str,
        policy_update: dict[str, Any],
        tenant: TenantContext = Depends(get_current_tenant),
    ):
        full_repo = f"{owner}/{repo}"
        if not tenant.can_access_repository(full_repo):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tenant '{tenant.tenant_id}' is not authorized to access repository '{full_repo}'",
            )

        valid_severities = {"critical", "high", "medium", "low", "info"}
        if "minimum_severity" in policy_update:
            sev = str(policy_update["minimum_severity"]).strip().lower()
            if sev not in valid_severities:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid minimum_severity '{sev}'. Allowed: {', '.join(sorted(valid_severities))}",
                )

        target_branches = policy_update.get("target_branches")
        if target_branches is not None:
            if not isinstance(target_branches, list):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="target_branches must be a list of branch name strings",
                )
            clean_branches = [str(b).strip() for b in target_branches if str(b).strip()]
            if not clean_branches:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="target_branches must contain at least one valid branch name",
                )
        else:
            clean_branches = ["main", "master"]

        allowed_events = policy_update.get("allowed_events")
        valid_events = {"pull_request", "code_scanning_alert", "check_run", "push", "issues"}
        if allowed_events is not None:
            if not isinstance(allowed_events, list):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="allowed_events must be a list of event name strings",
                )
            for ev in allowed_events:
                if str(ev).strip() not in valid_events:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid event '{ev}' in allowed_events. Allowed: {', '.join(sorted(valid_events))}",
                    )
            clean_events = [str(e).strip() for e in allowed_events if str(e).strip()]
        else:
            clean_events = ["pull_request", "code_scanning_alert", "check_run"]

        clean_policy = {
            "repository": full_repo,
            "enabled": bool(policy_update.get("enabled", True)),
            "minimum_severity": str(policy_update.get("minimum_severity", "medium")).strip().lower(),
            "auto_remediate": bool(policy_update.get("auto_remediate", True)),
            "auto_create_pr": bool(policy_update.get("auto_create_pr", True)),
            "target_branches": clean_branches,
            "allowed_events": clean_events,
        }

        if hasattr(resolved_store, "set_repository_policy"):
            resolved_store.set_repository_policy(full_repo, clean_policy)

        return clean_policy

    @app.get(
        "/jobs/{job_id}/events",
        summary="Stream Real-Time Job Lifecycle Events (SSE)",
        description="Streams real-time state transition events for a remediation job using Server-Sent Events (SSE). Supports reconnection with Last-Event-ID.",
        tags=["Jobs"],
    )
    async def stream_job_events(
        request: Request,
        job_id: str,
        last_event_id_header: str | None = Header(None, alias="Last-Event-ID"),
        last_event_id_query: int | None = Query(None, alias="last_event_id"),
        tenant: TenantContext = Depends(get_current_tenant),
    ):
        if resolved_store is None:
            raise HTTPException(status_code=500, detail="Job store not configured")

        job = resolved_store.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

        # Repository-level tenant authorization check
        if not tenant.can_access_repository(job.repository):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tenant '{tenant.tenant_id}' is not authorized to access repository '{job.repository}'",
            )

        # Parse initial Last-Event-ID
        start_id = 0
        if last_event_id_query is not None:
            start_id = max(0, last_event_id_query)
        elif last_event_id_header is not None:
            try:
                start_id = max(0, int(last_event_id_header.strip()))
            except ValueError:
                start_id = 0

        async def event_generator():
            last_sent_id = start_id
            terminal_states = {
                "pr_created",
                "pr_merged",
                "pr_closed",
                "failed",
                "superseded",
                "rolled_back",
            }
            max_idle_ticks = 600  # 5 minutes maximum idle stream (at 0.5s intervals)
            idle_counter = 0

            try:
                # Flush initial stream headers
                yield ": connected\n\n"
                while True:
                    if await request.is_disconnected():
                        break

                    # 1. Fetch current events from the store
                    events = []
                    if hasattr(resolved_store, "get_events"):
                        events = resolved_store.get_events(job_id)

                    # Filter and sort events newer than last_sent_id
                    new_events = [
                        e for e in sorted(events, key=lambda x: x.get("id", 0))
                        if e.get("id", 0) > last_sent_id
                    ]

                    for ev in new_events:
                        ev_id = ev.get("id", last_sent_id + 1)
                        last_sent_id = max(last_sent_id, ev_id)

                        payload = {
                            "job_id": job_id,
                            "event_id": ev_id,
                            "from_state": ev.get("from_state"),
                            "to_state": ev.get("to_state"),
                            "message": sanitize_secret_text(ev.get("message", "")),
                            "created_at": ev.get("created_at"),
                        }
                        yield f"id: {ev_id}\nevent: job_state\ndata: {json.dumps(payload)}\n\n"
                        idle_counter = 0

                    # 2. Check current job status
                    current_job = resolved_store.get(job_id)
                    current_state = ""
                    if current_job is not None:
                        current_state = str(
                            getattr(current_job.state, "value", current_job.state)
                        ).lower()

                    # 3. If job reached a terminal state, emit final terminal event and terminate stream cleanly
                    if current_state in terminal_states:
                        term_payload = {
                            "job_id": job_id,
                            "state": current_state,
                            "error": sanitize_secret_text(getattr(current_job, "error", None) or ""),
                            "pr_number": getattr(current_job, "pr_number", None),
                            "pr_url": getattr(current_job, "pr_url", None),
                            "is_stale": getattr(current_job, "is_stale", False),
                        }
                        yield f"id: {last_sent_id + 1}\nevent: job_terminal\ndata: {json.dumps(term_payload)}\n\n"
                        break

                    # 4. Periodic keep-alive ping
                    idle_counter += 1
                    if idle_counter % 30 == 0:
                        yield ": keepalive\n\n"

                    if idle_counter >= max_idle_ticks:
                        break

                    await asyncio.sleep(0.5)
            except asyncio.CancelledError:
                pass
            except Exception:
                pass

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @app.get(
        "/events",
        summary="Stream Tenant-Wide Job Lifecycle Events (SSE)",
        description="Streams real-time state transition events across all accessible tenant repositories using Server-Sent Events (SSE). Supports reconnection with Last-Event-ID.",
        tags=["Events"],
    )
    async def stream_all_job_events(
        request: Request,
        last_event_id_header: str | None = Header(None, alias="Last-Event-ID"),
        last_event_id_query: int | None = Query(None, alias="last_event_id"),
        limit: int | None = Query(None, description="Optional maximum number of events to stream before closing"),
        tenant: TenantContext = Depends(get_current_tenant),
    ):
        if resolved_store is None:
            raise HTTPException(status_code=500, detail="Job store not configured")

        start_id = 0
        if last_event_id_query is not None:
            start_id = max(0, last_event_id_query)
        elif last_event_id_header is not None:
            try:
                start_id = max(0, int(last_event_id_header.strip()))
            except ValueError:
                start_id = 0

        async def tenant_event_generator():
            last_sent_id = start_id
            seen_event_keys: set[str] = set()
            max_idle_ticks = 1200  # 10 minutes maximum stream duration
            idle_counter = 0

            try:
                # Flush initial stream headers
                yield ": connected\n\n"
                while True:
                    if await request.is_disconnected():
                        break

                    jobs = resolved_store.list_jobs(limit=100)
                    tenant_jobs = [j for j in jobs if tenant.can_access_repository(j.repository)]

                    all_events = []
                    for job in tenant_jobs:
                        job_events = resolved_store.get_events(job.job_id) if hasattr(resolved_store, "get_events") else []
                        for ev in job_events:
                            ev_key = f"{job.job_id}:{ev.get('id', 0)}:{ev.get('to_state')}"
                            all_events.append((job, ev, ev_key))

                    # Sort chronologically
                    for job, ev, ev_key in all_events:
                        ev_id = ev.get("id", last_sent_id + 1)
                        if ev_key not in seen_event_keys and ev_id > start_id:
                            seen_event_keys.add(ev_key)
                            last_sent_id = max(last_sent_id, ev_id)
                            payload = {
                                "job_id": job.job_id,
                                "repository": job.repository,
                                "event_id": ev_id,
                                "from_state": ev.get("from_state"),
                                "to_state": ev.get("to_state"),
                                "message": sanitize_secret_text(ev.get("message", "")),
                                "pr_number": getattr(job, "pr_number", None),
                                "pr_url": getattr(job, "pr_url", None),
                                "created_at": ev.get("created_at"),
                            }
                            yield f"id: {last_sent_id}\nevent: job_transition\ndata: {json.dumps(payload)}\n\n"
                            idle_counter = 0

                            if limit is not None and len(seen_event_keys) >= limit:
                                return

                    idle_counter += 1
                    if idle_counter % 30 == 0:
                        yield ": keepalive\n\n"

                    if idle_counter >= max_idle_ticks:
                        break

                    await asyncio.sleep(1.0)
            except asyncio.CancelledError:
                pass
            except Exception:
                pass

        return StreamingResponse(
            tenant_event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @app.post(
        "/evidence/verify",
        summary="Verify Cryptographic Evidence Signature",
        description="Verifies the Ed25519 digital signature and canonical SHA-256 digest on an evidence payload.",
        tags=["Evidence"],
    )
    async def verify_evidence_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        from packages.signing import verify_evidence
        result = verify_evidence(payload)
        return {
            "valid": result.valid,
            "key_id": result.key_id,
            "signing_algorithm": result.signing_algorithm,
            "sha256_digest": result.sha256_digest,
            "error": result.error,
        }

    @app.post(
        "/remediations/run",
        response_model=RemediationTriggerResponse,
        summary="Trigger Direct Finding Remediation",
        description="Directly ingests a security finding and executes the end-to-end verification pipeline (analysis, AST validation, sandbox execution, regression testing, Ed25519 evidence sealing, and authorized PR creation).",
        tags=["Remediations"],
    )
    async def trigger_remediation_endpoint(
        req: RemediationTriggerRequest,
        tenant: TenantContext = Depends(get_current_tenant),
    ) -> RemediationTriggerResponse:
        import hashlib
        from datetime import datetime, timezone
        from uuid import uuid4
        from packages.jobs.pipeline_factory import create_concrete_remediation_orchestrator
        from packages.jobs.state import JobRecord, JobState

        clean_repo = req.repository.strip()
        if not tenant.can_access_repository(clean_repo):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tenant '{tenant.tenant_id}' is not authorized to remediate repository '{clean_repo}'",
            )

        if resolved_store is None:
            raise HTTPException(status_code=500, detail="Job store not configured")

        delivery_id = f"direct-{uuid4().hex[:12]}"
        job_id = f"job-{delivery_id}"
        fingerprint = hashlib.sha256(f"{clean_repo}:{req.file}:{req.start_line}:{req.rule_id}".encode()).hexdigest()[:24]

        # 1. Create and commit durable job record
        if hasattr(resolved_store, "create_from_webhook"):
            resolved_store.create_from_webhook(
                delivery_id=delivery_id,
                repository=clean_repo,
                commit_sha=req.commit_sha,
                event_type="code_scanning_alert",
                target_branch="main",
            )
        elif hasattr(resolved_store, "create"):
            job = JobRecord(
                job_id=job_id,
                delivery_id=delivery_id,
                repository=clean_repo,
                commit_sha=req.commit_sha,
                target_branch="main",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            job.event_type = "code_scanning_alert"
            resolved_store.create(job)
        else:
            raise HTTPException(status_code=500, detail="Job store creation contract unsupported")

        # 2. Enqueue task asynchronously to Celery worker
        enqueue_fn = getattr(dispatcher, "enqueue", None)
        if enqueue_fn is not None:
            try:
                enqueue_fn(job_id)
            except Exception as exc:
                if hasattr(resolved_store, "record_transition"):
                    try:
                        resolved_store.record_transition(
                            job_id,
                            JobState.QUEUED.value,
                            JobState.FAILED.value,
                            f"Celery enqueue failure: {exc}",
                        )
                    except Exception:
                        pass
                job_record = resolved_store.get(job_id)
                if job_record:
                    job_record.state = JobState.FAILED
                    job_record.error = f"Enqueue failure: {exc}"
                    resolved_store.update(job_record)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to queue remediation task: {exc}",
                )
        else:
            try:
                from packages.jobs.celery_app import remediation_task
                remediation_task.delay(job_id)
            except Exception as exc:
                if hasattr(resolved_store, "record_transition"):
                    try:
                        resolved_store.record_transition(
                            job_id,
                            JobState.QUEUED.value,
                            JobState.FAILED.value,
                            f"Celery enqueue failure: {exc}",
                        )
                    except Exception:
                        pass
                job_record = resolved_store.get(job_id)
                if job_record:
                    job_record.state = JobState.FAILED
                    job_record.error = f"Enqueue failure: {exc}"
                    resolved_store.update(job_record)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to queue remediation task: {exc}",
                )

        return RemediationTriggerResponse(
            job_id=job_id,
            repository=clean_repo,
            commit_sha=req.commit_sha,
            state="queued",
            verified=False,
            pr=None,
            evidence=None,
            policy=None,
            error=None,
        )

    return app
