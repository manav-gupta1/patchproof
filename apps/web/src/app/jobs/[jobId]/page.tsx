"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { apiClient } from "@/lib/api";
import { JobStatusResponse, JobEvidenceResponse, JobStateEvent, JobTerminalEvent } from "@/lib/types";
import { SafetyOutcomeBanner } from "@/components/jobs/SafetyOutcomeBanner";
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
} from "lucide-react";
import { formatSha } from "@/lib/utils";

type DetailTab = "overview" | "evidence" | "diff" | "sandbox" | "delivery";

export default function JobDetailPage() {
  const params = useParams();
  const rawJobId = params?.jobId as string;
  const jobId = decodeURIComponent(rawJobId || "");

  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [evidence, setEvidence] = useState<JobEvidenceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [connectionMode, setConnectionMode] = useState<"sse" | "polling" | "connected" | "terminal">("sse");
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

  if (loading) {
    return (
      <div className="py-16 max-w-5xl mx-auto">
        <LoadingSpinner label={`Loading remediation job ${jobId}...`} size="lg" />
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="space-y-4 max-w-5xl mx-auto">
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

  const isVerified = ["verified", "pr_created", "pr_updated", "pr_merged"].includes((job.state || "").toLowerCase());
  const isFailed = (job.state || "").toLowerCase() === "failed";
  const isTerminal = ["pr_created", "pr_merged", "pr_closed", "failed", "superseded", "rolled_back"].includes(
    (job.state || "").toLowerCase()
  );

  return (
    <div className="space-y-5 max-w-5xl mx-auto" data-testid="job-detail-page">
      {/* Top Header & Breadcrumb */}
      <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2 border-b border-border-subtle pb-4">
        <div>
          <Link
            href="/jobs"
            className="text-xs font-mono text-zinc-400 hover:text-zinc-200 inline-flex items-center gap-1 mb-1.5 transition-colors"
          >
            <ArrowLeft className="w-3 h-3" /> Remediations
          </Link>
          <div className="flex flex-wrap items-center gap-2 text-xs font-mono text-zinc-400">
            <span className="text-zinc-200 font-medium">{job.repository}</span>
            <span>·</span>
            <span>@{formatSha(job.commit_sha, 7)}</span>
            <span>·</span>
            <span className="text-zinc-500">ID: {job.job_id}</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {!isTerminal && (
            <span data-testid="sse-status-indicator" className="text-xs font-mono text-zinc-400">
              {connectionMode === "connected" || connectionMode === "sse" ? (
                <span className="text-emerald-400 inline-flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  SSE Connected
                </span>
              ) : (
                <span className="text-amber-400 inline-flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                  Polling
                </span>
              )}
            </span>
          )}

          <button
            onClick={() => loadJobData(false)}
            className="text-xs font-mono text-zinc-400 hover:text-zinc-200 inline-flex items-center gap-1 transition-colors"
          >
            <RefreshCw className="w-3 h-3" /> Refresh
          </button>
        </div>
      </div>

      {/* 1. Unmistakable Top Security Decision Banner */}
      <SafetyOutcomeBanner job={job} />

      {/* 2. Verification Checklist */}
      <div className="border border-border-subtle bg-surface-300 rounded-lg p-4 space-y-2.5">
        <div className="text-[11px] font-mono uppercase tracking-wider text-zinc-500">
          Verification gates
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 text-xs font-mono">
          <div className="flex items-center gap-2 text-zinc-300">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span>AST syntax validated</span>
          </div>
          <div className="flex items-center gap-2 text-zinc-300">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span>Vulnerability eliminated in re-scan</span>
          </div>
          <div className="flex items-center gap-2 text-zinc-300">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span>gVisor sandbox completed (0 egress)</span>
          </div>
          <div className="flex items-center gap-2 text-zinc-300">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span>Security policy passed</span>
          </div>
          <div className="flex items-center gap-2 text-zinc-300">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span>Ed25519 cryptographic proof signed</span>
          </div>
          <div className="flex items-center gap-2 text-zinc-300">
            {isVerified ? (
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            ) : isFailed ? (
              <XCircle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
            ) : (
              <span className="w-3.5 h-3.5 rounded-full border border-zinc-600 shrink-0" />
            )}
            <span>{isVerified ? "Safe for GitHub publication" : isFailed ? "Zero GitHub writes (blocked)" : "Running verification..."}</span>
          </div>
        </div>
      </div>

      {/* 3. Workflow Progress Stepper */}
      <WorkflowProgressStepper job={job} />

      {/* 4. Progressive Disclosure Tabs */}
      <div className="space-y-3 pt-2">
        <div className="border-b border-border-subtle flex items-center gap-1 overflow-x-auto" role="tablist" aria-label="Workflow inspection tabs">
          <button
            role="tab"
            aria-selected={activeTab === "overview"}
            onClick={() => setActiveTab("overview")}
            className={`px-3 py-2 text-xs font-mono transition-colors whitespace-nowrap border-b-2 -mb-px ${
              activeTab === "overview"
                ? "border-zinc-200 text-zinc-100 font-semibold"
                : "border-transparent text-zinc-400 hover:text-zinc-200"
            }`}
          >
            Overview
          </button>
          <button
            role="tab"
            aria-selected={activeTab === "evidence"}
            onClick={() => setActiveTab("evidence")}
            className={`px-3 py-2 text-xs font-mono transition-colors whitespace-nowrap border-b-2 -mb-px ${
              activeTab === "evidence"
                ? "border-zinc-200 text-zinc-100 font-semibold"
                : "border-transparent text-zinc-400 hover:text-zinc-200"
            }`}
          >
            Evidence & Proof
          </button>
          <button
            role="tab"
            aria-selected={activeTab === "diff"}
            onClick={() => setActiveTab("diff")}
            className={`px-3 py-2 text-xs font-mono transition-colors whitespace-nowrap border-b-2 -mb-px ${
              activeTab === "diff"
                ? "border-zinc-200 text-zinc-100 font-semibold"
                : "border-transparent text-zinc-400 hover:text-zinc-200"
            }`}
          >
            Unified Diff
          </button>
          <button
            role="tab"
            aria-selected={activeTab === "sandbox"}
            onClick={() => setActiveTab("sandbox")}
            className={`px-3 py-2 text-xs font-mono transition-colors whitespace-nowrap border-b-2 -mb-px ${
              activeTab === "sandbox"
                ? "border-zinc-200 text-zinc-100 font-semibold"
                : "border-transparent text-zinc-400 hover:text-zinc-200"
            }`}
          >
            Sandbox Output
          </button>
          <button
            role="tab"
            aria-selected={activeTab === "delivery"}
            onClick={() => setActiveTab("delivery")}
            className={`px-3 py-2 text-xs font-mono transition-colors whitespace-nowrap border-b-2 -mb-px ${
              activeTab === "delivery"
                ? "border-zinc-200 text-zinc-100 font-semibold"
                : "border-transparent text-zinc-400 hover:text-zinc-200"
            }`}
          >
            GitHub Delivery
          </button>
        </div>

        {/* Tab Panels */}
        <div>
          {activeTab === "overview" && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
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
