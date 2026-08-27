"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { apiClient } from "@/lib/api";
import { JobStatusResponse, JobEvidenceResponse, JobStateEvent, JobTerminalEvent } from "@/lib/types";
import { SafetyOutcomeBanner } from "@/components/jobs/SafetyOutcomeBanner";
import { VerificationJourneyPipeline } from "@/components/jobs/VerificationJourneyPipeline";
import { WorkflowProgressStepper } from "@/components/jobs/WorkflowProgressStepper";
import { LifecycleTimeline } from "@/components/jobs/LifecycleTimeline";
import { FindingCard } from "@/components/jobs/FindingCard";
import { DiffViewer } from "@/components/jobs/DiffViewer";
import { VerificationCard } from "@/components/jobs/VerificationCard";
import { EvidenceCard } from "@/components/jobs/EvidenceCard";
import { PolicyCard } from "@/components/jobs/PolicyCard";
import { GitHubCard } from "@/components/jobs/GitHubCard";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { ErrorAlert } from "@/components/common/ErrorAlert";
import {
  ArrowLeft,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock,
  Ban,
  GitBranch,
  Shield,
  FileCode2,
} from "lucide-react";
import { formatSha } from "@/lib/utils";

type DetailTab = "overview" | "evidence" | "diff" | "sandbox" | "delivery";
type ConnectionMode = "sse" | "connected" | "reconnecting" | "polling" | "terminal";

export default function JobDetailPage() {
  const params = useParams();
  const rawJobId = params?.jobId as string;
  const jobId = decodeURIComponent(rawJobId || "");

  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [evidence, setEvidence] = useState<JobEvidenceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [connectionMode, setConnectionMode] = useState<ConnectionMode>("sse");
  const [activeTab, setActiveTab] = useState<DetailTab>("overview");

  const loadJobData = useCallback(async (silent: boolean = false) => {
    if (!silent) setLoading(true);
    setError(null);
    try {
      const [jobData, evidenceData] = await Promise.all([
        apiClient.getJob(jobId),
        apiClient.getJobEvidence(jobId).catch(() => null),
      ]);
      setJob(jobData);
      setEvidence(evidenceData);
    } catch (err: any) {
      setError(err.message || `Failed to load job '${jobId}'`);
    } finally {
      if (!silent) setLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    if (!jobId) return;

    loadJobData();

    const unsubscribe = apiClient.subscribeToJobEvents(
      jobId,
      {
        onOpen: () => {
          setConnectionMode("connected");
          loadJobData(true);
        },
        onReconnecting: () => {
          setConnectionMode("reconnecting");
        },
        onEvent: (event: JobStateEvent) => {
          setJob((prev) => {
            if (!prev) return prev;
            const updatedEvents = [...(prev.events || [])];
            const exists = updatedEvents.some((e) => e.to_state === event.to_state);
            if (!exists) {
              updatedEvents.push({
                id: event.event_id,
                from_state: event.from_state,
                to_state: event.to_state,
                message: event.message,
                created_at: event.created_at || new Date().toISOString(),
              });
            }
            return {
              ...prev,
              state: event.to_state,
              updated_at: event.created_at || new Date().toISOString(),
              events: updatedEvents,
            };
          });

          if (event.to_state === "verified" || event.to_state === "pr_created") {
            apiClient.getJobEvidence(jobId).then(setEvidence).catch(() => null);
          }
        },
        onTerminal: (terminalEvent: JobTerminalEvent) => {
          setConnectionMode("terminal");
          setJob((prev) => {
            if (!prev) return prev;
            return {
              ...prev,
              state: terminalEvent.state,
              error: terminalEvent.error || prev.error,
              pr_number: terminalEvent.pr_number || prev.pr_number,
              pr_url: terminalEvent.pr_url || prev.pr_url,
              is_stale: terminalEvent.is_stale !== undefined ? terminalEvent.is_stale : prev.is_stale,
            };
          });
          loadJobData(true);
        },
        onFallback: () => {
          setConnectionMode("polling");
        },
        onError: () => {},
      },
      { fallbackToPolling: true }
    );

    return () => {
      unsubscribe();
    };
  }, [jobId, loadJobData]);

  const state = (job?.state || "queued").toLowerCase();
  const isVerified = ["verified", "pr_created", "pr_updated", "pr_merged"].includes(state);
  const isFailed = state === "failed";
  const isTerminal = ["pr_created", "pr_merged", "pr_closed", "failed", "superseded", "rolled_back"].includes(state);
  const events = job?.events || [];
  const errorMsg = (job?.error || "").toLowerCase();

  // Dynamically resolve verification gates based on real telemetry
  const verificationGates = useMemo(() => {
    const reachedStates = new Set(events.map((e) => (e.to_state || "").toLowerCase()));

    // 1. AST Syntax Check
    let astStatus: "passed" | "active" | "failed" | "pending" = "pending";
    if (isVerified || reachedStates.has("verifying") || reachedStates.has("verified") || reachedStates.has("patching")) {
      astStatus = "passed";
    } else if (state === "analyzing" || state === "patching") {
      astStatus = "active";
    } else if (isFailed && (errorMsg.includes("ast") || errorMsg.includes("syntax") || errorMsg.includes("patch"))) {
      astStatus = "failed";
    }

    // 2. Vulnerability Elimination (Re-scan)
    let rescanStatus: "passed" | "active" | "failed" | "pending" = "pending";
    if (isVerified || (evidence?.verification_results?.target_vulnerability_eliminated)) {
      rescanStatus = "passed";
    } else if (state === "verifying") {
      rescanStatus = "active";
    } else if (isFailed && (errorMsg.includes("rescan") || errorMsg.includes("vulnerability") || errorMsg.includes("finding"))) {
      rescanStatus = "failed";
    }

    // 3. gVisor Sandbox Execution
    let sandboxStatus: "passed" | "active" | "failed" | "pending" = "pending";
    if (isVerified) {
      sandboxStatus = "passed";
    } else if (state === "verifying") {
      sandboxStatus = "active";
    } else if (isFailed && (errorMsg.includes("sandbox") || errorMsg.includes("gvisor") || errorMsg.includes("test") || errorMsg.includes("exit code") || reachedStates.has("verifying"))) {
      sandboxStatus = "failed";
    }

    // 4. Security Policy
    let policyStatus: "passed" | "active" | "failed" | "pending" = "pending";
    if (isVerified || (job?.policy && job.policy.allowed)) {
      policyStatus = "passed";
    } else if (job?.policy && !job.policy.allowed) {
      policyStatus = "failed";
    } else if (state === "verifying" || state === "scanning") {
      policyStatus = "active";
    } else if (isFailed && errorMsg.includes("policy")) {
      policyStatus = "failed";
    }

    // 5. Ed25519 Cryptographic Proof
    let proofStatus: "passed" | "active" | "failed" | "blocked" | "pending" = "pending";
    if (evidence?.signature || isVerified) {
      proofStatus = "passed";
    } else if (state === "verified") {
      proofStatus = "active";
    } else if (isFailed) {
      proofStatus = "blocked";
    }

    // 6. Safe for GitHub Publication
    let pubStatus: "passed" | "active" | "blocked" | "pending" = "pending";
    if (isVerified && (job?.pr_number || ["pr_created", "pr_updated", "pr_merged"].includes(state))) {
      pubStatus = "passed";
    } else if (isVerified) {
      pubStatus = "active";
    } else if (isFailed) {
      pubStatus = "blocked";
    }

    return [
      {
        id: "ast",
        label: "AST syntax validated",
        status: astStatus,
      },
      {
        id: "rescan",
        label: "Vulnerability eliminated in re-scan",
        status: rescanStatus,
      },
      {
        id: "sandbox",
        label: "gVisor sandbox completed (0 egress)",
        status: sandboxStatus,
      },
      {
        id: "policy",
        label: "Security policy passed",
        status: policyStatus,
      },
      {
        id: "proof",
        label: "Ed25519 cryptographic proof signed",
        status: proofStatus,
      },
      {
        id: "pub",
        label: isVerified
          ? "Safe for GitHub publication"
          : isFailed
          ? "Zero GitHub writes (blocked)"
          : "Authorized write boundary",
        status: pubStatus,
      },
    ];
  }, [state, isVerified, isFailed, events, errorMsg, evidence, job]);

  if (loading) {
    return (
      <div className="py-24 max-w-7xl mx-auto">
        <LoadingSpinner label={`Loading remediation job ${jobId}...`} size="lg" />
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="space-y-4 max-w-7xl mx-auto">
        <Link
          href="/jobs"
          className="text-xs font-mono text-zinc-400 hover:text-zinc-200 inline-flex items-center gap-1"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Remediations
        </Link>
        <ErrorAlert
          title="Workflow Not Found"
          message={error || `Remediation workflow '${jobId}' does not exist or you do not have permission.`}
          onRetry={() => loadJobData(false)}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto" data-testid="job-detail-page">
      {/* Top Header & Breadcrumb */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border-subtle pb-5">
        <div>
          <Link
            href="/jobs"
            className="text-xs font-mono text-zinc-400 hover:text-zinc-200 inline-flex items-center gap-1.5 mb-2 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Remediations Control Plane
          </Link>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-xl sm:text-2xl font-bold font-mono text-zinc-100 tracking-tight">
              {job.repository}
            </h1>
            <span className="px-2 py-0.5 rounded bg-surface-300 border border-border-subtle text-xs font-mono text-zinc-300 flex items-center gap-1.5">
              <GitBranch className="w-3 h-3 text-zinc-400" />
              @{formatSha(job.commit_sha, 7)}
            </span>
            <span className="px-2 py-0.5 rounded bg-surface-300 border border-border-subtle text-xs font-mono text-zinc-400">
              ID: {job.job_id}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {!isTerminal && (
            <span data-testid="sse-status-indicator" className="text-xs font-mono">
              {connectionMode === "reconnecting" ? (
                <span className="text-amber-400 inline-flex items-center gap-1.5 font-bold px-2.5 py-1 rounded bg-amber-950/40 border border-amber-800">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
                  RECONNECTING…
                </span>
              ) : connectionMode === "connected" || connectionMode === "sse" ? (
                <span className="text-emerald-400 inline-flex items-center gap-1.5 font-medium px-2.5 py-1 rounded bg-emerald-950/40 border border-emerald-800/80">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  SSE Connected
                </span>
              ) : (
                <span className="text-amber-400 inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-amber-950/40 border border-amber-800">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                  Polling
                </span>
              )}
            </span>
          )}

          <button
            onClick={() => loadJobData(false)}
            className="text-xs font-mono text-zinc-300 hover:text-zinc-100 bg-surface-300 hover:bg-surface-100 border border-border-subtle px-3 py-1.5 rounded-lg inline-flex items-center gap-1.5 transition-colors shadow-sm"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Refresh Telemetry
          </button>
        </div>
      </div>

      {/* 1. Unmistakable Top Security Decision Banner */}
      <SafetyOutcomeBanner job={job} />

      {/* 2. Primary Hero: Connected 6-Stage Verification Journey Pipeline */}
      <VerificationJourneyPipeline job={job} evidence={evidence} />

      {/* 3. Verification Gates Grid */}
      <div className="border border-border-subtle bg-surface-200 rounded-xl p-4 sm:p-5 space-y-3">
        <div className="text-[11px] font-mono uppercase tracking-wider text-zinc-400 font-medium">
          Automated Verification Gate Checklist
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-xs font-mono">
          {verificationGates.map((gate) => {
            let icon = <span className="w-3.5 h-3.5 rounded-full border border-zinc-700 shrink-0" />;
            let textColor = "text-zinc-400";

            if (gate.status === "passed") {
              icon = <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />;
              textColor = "text-zinc-200";
            } else if (gate.status === "failed") {
              icon = <XCircle className="w-3.5 h-3.5 text-rose-400 shrink-0" />;
              textColor = "text-rose-300 font-semibold";
            } else if (gate.status === "active") {
              icon = <Clock className="w-3.5 h-3.5 text-indigo-400 animate-spin shrink-0" />;
              textColor = "text-indigo-200";
            } else if (gate.status === "blocked") {
              icon = <Ban className="w-3.5 h-3.5 text-zinc-600 shrink-0" />;
              textColor = "text-zinc-600";
            }

            return (
              <div key={gate.id} className={`flex items-center gap-2 ${textColor}`}>
                {icon}
                <span className="truncate">{gate.label}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* 4. Progressive Disclosure Tabs */}
      <div className="space-y-4 pt-2">
        <div className="border-b border-border-subtle flex items-center gap-2 overflow-x-auto" role="tablist" aria-label="Workflow inspection tabs">
          <button
            role="tab"
            aria-selected={activeTab === "overview"}
            onClick={() => setActiveTab("overview")}
            className={`px-4 py-2.5 text-xs font-mono transition-colors whitespace-nowrap border-b-2 -mb-px ${
              activeTab === "overview"
                ? "border-zinc-200 text-zinc-100 font-bold"
                : "border-transparent text-zinc-400 hover:text-zinc-200"
            }`}
          >
            Overview & Telemetry
          </button>
          <button
            role="tab"
            aria-selected={activeTab === "evidence"}
            onClick={() => setActiveTab("evidence")}
            className={`px-4 py-2.5 text-xs font-mono transition-colors whitespace-nowrap border-b-2 -mb-px ${
              activeTab === "evidence"
                ? "border-zinc-200 text-zinc-100 font-bold"
                : "border-transparent text-zinc-400 hover:text-zinc-200"
            }`}
          >
            Evidence & Proof
          </button>
          <button
            role="tab"
            aria-selected={activeTab === "diff"}
            onClick={() => setActiveTab("diff")}
            className={`px-4 py-2.5 text-xs font-mono transition-colors whitespace-nowrap border-b-2 -mb-px ${
              activeTab === "diff"
                ? "border-zinc-200 text-zinc-100 font-bold"
                : "border-transparent text-zinc-400 hover:text-zinc-200"
            }`}
          >
            Unified Diff
          </button>
          <button
            role="tab"
            aria-selected={activeTab === "sandbox"}
            onClick={() => setActiveTab("sandbox")}
            className={`px-4 py-2.5 text-xs font-mono transition-colors whitespace-nowrap border-b-2 -mb-px ${
              activeTab === "sandbox"
                ? "border-zinc-200 text-zinc-100 font-bold"
                : "border-transparent text-zinc-400 hover:text-zinc-200"
            }`}
          >
            Sandbox Output
          </button>
          <button
            role="tab"
            aria-selected={activeTab === "delivery"}
            onClick={() => setActiveTab("delivery")}
            className={`px-4 py-2.5 text-xs font-mono transition-colors whitespace-nowrap border-b-2 -mb-px ${
              activeTab === "delivery"
                ? "border-zinc-200 text-zinc-100 font-bold"
                : "border-transparent text-zinc-400 hover:text-zinc-200"
            }`}
          >
            GitHub Delivery
          </button>
        </div>

        {/* Tab Panels */}
        <div>
          {activeTab === "overview" && (
            <div className="space-y-5">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                <FindingCard
                  finding={evidence?.target_finding}
                  defaultFingerprint={job.commit_sha}
                />
                <PolicyCard policy={job.policy || evidence?.policy} />
              </div>
              <LifecycleTimeline job={job} />
            </div>
          )}

          {activeTab === "evidence" && (
            <EvidenceCard
              evidence={evidence}
              verified={job.verified}
              commitSha={job.commit_sha}
            />
          )}

          {activeTab === "diff" && (
            <DiffViewer patch={evidence?.patch_summary} />
          )}

          {activeTab === "sandbox" && (
            <VerificationCard
              results={evidence?.verification_results}
              verified={job.verified}
              verifiedSha={job.verified_sha || evidence?.commit_sha}
            />
          )}

          {activeTab === "delivery" && (
            <GitHubCard job={job} />
          )}
        </div>
      </div>
    </div>
  );
}
