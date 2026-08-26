export type JobLifecycleState =
  | "queued"
  | "scanning"
  | "analyzing"
  | "patching"
  | "verifying"
  | "verified"
  | "pr_created"
  | "pr_updated"
  | "pr_closed"
  | "pr_merged"
  | "superseded"
  | "rolled_back"
  | "failed";

export interface JobEvent {
  id?: number | null;
  from_state?: string | null;
  to_state: string;
  message: string;
  created_at?: string | null;
}

export interface PullRequestInfo {
  number: number;
  url: string;
  head_sha?: string | null;
  branch?: string | null;
  base_branch?: string | null;
  repository?: string | null;
}

export interface TargetFindingInfo {
  rule_id: string;
  fingerprint: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO" | string;
  file?: string | null;
  line?: number | null;
  scanner?: string | null;
  description?: string | null;
  code_context?: string | null;
}

export interface VerificationCheck {
  name: string;
  status: "passed" | "failed" | "skipped";
  duration_ms?: number;
  message?: string;
}

export interface VerificationResultsInfo {
  rescan_findings_count: number;
  target_vulnerability_eliminated: boolean;
  verification_status: "passed" | "failed" | string;
  test_summary?: string | null;
  checks?: VerificationCheck[] | null;
  sandbox_provider?: string;
  network_policy?: string;
  execution_duration_sec?: number;
  resource_limits?: {
    memory_mb: number;
    cpu_limit: number;
  };
}

export interface PatchSummaryInfo {
  title: string;
  files_changed: string[];
  head_branch?: string | null;
  base_branch?: string | null;
  explanation?: string | null;
  diff?: string | null;
  original_code?: string | null;
  proposed_patch?: string | null;
}

export interface PolicyDecision {
  allowed: boolean;
  action: string;
  reason: string;
  rule_id?: string | null;
  severity?: string | null;
  auto_remediate?: boolean;
  auto_create_pr?: boolean;
  policy_source?: string;
  policy_version?: string;
  target_branch?: string | null;
  event_type?: string | null;
}

export interface JobStatusResponse {
  job_id: string;
  repository: string;
  commit_sha: string;
  event_type: string;
  target_branch?: string | null;
  state: JobLifecycleState | string;
  lifecycle_state?: string | null;
  verified?: boolean | null;
  pr?: PullRequestInfo | null;
  pr_number?: number | null;
  pr_url?: string | null;
  remediation_branch?: string | null;
  current_head_sha?: string | null;
  verified_sha?: string | null;
  merge_commit_sha?: string | null;
  is_stale: boolean;
  invalidation_reason?: string | null;
  invalidated_by_sha?: string | null;
  policy?: PolicyDecision | null;
  error?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  events: JobEvent[];
}

export interface JobEvidenceResponse {
  evidence_id: string;
  job_id: string;
  commit_sha: string;
  repository: string;
  verified: boolean;
  finding_count: number;
  target_finding?: TargetFindingInfo | null;
  verification_results?: VerificationResultsInfo | null;
  patch_summary?: PatchSummaryInfo | null;
  pr?: PullRequestInfo | null;
  policy?: PolicyDecision | null;
  sha256_digest?: string | null;
  signature?: string | null;
  signing_algorithm?: string | null;
  signing_key_id?: string | null;
  signed_at?: string | null;
  generated_at?: string | null;
}

export interface JobListResponse {
  jobs: JobStatusResponse[];
  total: number;
  limit: number;
  offset: number;
}

export interface RepositorySummary {
  repository: string;
  installation_status: string;
  total_jobs: number;
  active_jobs: number;
  verified_prs: number;
  failed_jobs: number;
  last_job_id?: string | null;
  last_activity?: string | null;
}

export interface RepositoryListResponse {
  repositories: RepositorySummary[];
  total: number;
}

export interface SandboxStatusInfo {
  provider: string;
  network_policy: string;
  isolated: boolean;
  max_memory_mb: number;
  cpu_limit: number;
}

export interface SystemStatusResponse {
  api: "healthy" | "degraded" | "error" | string;
  worker: "healthy" | "degraded" | "error" | string;
  database: "healthy" | "degraded" | "error" | string;
  redis: "healthy" | "degraded" | "error" | string;
  sandbox: SandboxStatusInfo;
  auth_enabled: boolean;
  tenant?: string | null;
}

export interface SettingsStatusResponse {
  github_app_configured: boolean;
  webhook_configured: boolean;
  evidence_signing: {
    configured: boolean;
    key_id: string;
    algorithm: string;
    key_type: string;
  };
  sandbox: SandboxStatusInfo;
  auth_mode: string;
}

export interface EvidenceVerificationResult {
  valid: boolean;
  key_id?: string | null;
  signing_algorithm?: string | null;
  sha256_digest?: string | null;
  error?: string | null;
}

export interface JobStateEvent {
  job_id: string;
  event_id: number;
  from_state?: string | null;
  to_state: string;
  message: string;
  created_at?: string | null;
}

export interface JobTerminalEvent {
  job_id: string;
  state: string;
  error?: string | null;
  pr_number?: number | null;
  pr_url?: string | null;
  is_stale?: boolean;
}

export interface JobTransitionEvent {
  job_id: string;
  repository: string;
  event_id: number;
  from_state?: string | null;
  to_state: string;
  message: string;
  pr_number?: number | null;
  pr_url?: string | null;
  created_at?: string | null;
}

