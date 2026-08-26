"use client";

import React from "react";
import Link from "next/link";
import { ShieldAlert, AlertTriangle, CheckCircle2, ArrowRight, Lock } from "lucide-react";
import { JobStatusResponse } from "@/lib/types";

interface AttentionSectionProps {
  jobs: JobStatusResponse[];
}

export function AttentionSection({ jobs }: AttentionSectionProps) {
  const failedJobs = jobs.filter(
    (j) => (j.state || "").toLowerCase() === "failed"
  );
  const staleJobs = jobs.filter((j) => Boolean(j.is_stale));
  const activeJobs = jobs.filter((j) =>
    ["queued", "scanning", "analyzing", "patching", "verifying"].includes(
      (j.state || "").toLowerCase()
    )
  );

  const hasAttentionItems = failedJobs.length > 0 || staleJobs.length > 0 || activeJobs.length > 0;

  return (
    <div className="space-y-3 font-mono text-xs select-none" data-testid="attention-section">
      <div className="flex items-center justify-between pb-1 border-b border-border-subtle">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-3.5 h-3.5 text-zinc-400" />
          <span className="text-xs font-semibold text-zinc-100 uppercase tracking-wider">
            Security Attention & Invariant Alerts
          </span>
        </div>
        {hasAttentionItems && (
          <span className="text-[11px] text-zinc-400">
            {failedJobs.length + staleJobs.length + activeJobs.length} active events
          </span>
        )}
      </div>

      {!hasAttentionItems ? (
        <div
          className="p-3.5 rounded-md bg-surface-300 border border-border-subtle flex items-center justify-between gap-4"
          data-testid="attention-all-clear"
        >
          <div className="flex items-center gap-2.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 shrink-0" />
            <span className="font-semibold text-zinc-200">System Status: Nominal</span>
            <span className="text-zinc-600 hidden sm:inline">·</span>
            <span className="text-zinc-400 hidden sm:inline">
              Zero security violations or blocked writes pending review.
            </span>
          </div>
          <span className="text-[10px] text-emerald-400 bg-emerald-950/60 border border-emerald-800 px-2 py-0.5 rounded font-bold">
            ALL CLEAR
          </span>
        </div>
      ) : (
        <div className="space-y-2">
          {/* Failed / Blocked Jobs */}
          {failedJobs.map((job) => (
            <div
              key={job.job_id}
              className="p-3.5 rounded-md border border-rose-900/60 bg-rose-950/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
              data-testid={`attention-failed-${job.job_id}`}
            >
              <div className="flex items-start sm:items-center gap-3">
                <span className="w-2 h-2 rounded-full bg-rose-400 shrink-0 mt-1 sm:mt-0" />
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-bold text-rose-200">
                      WRITE BLOCKED: {job.repository}
                    </span>
                    <span className="px-1.5 py-0.2 rounded bg-rose-950 text-rose-300 border border-rose-800 text-[10px] font-bold">
                      FAIL-CLOSED ENFORCED
                    </span>
                  </div>
                  <p className="text-zinc-300 text-[11px] mt-0.5">
                    {job.error || "Automated sandbox tests failed. Invariant enforced: 0 remote writes."}
                  </p>
                </div>
              </div>

              <Link
                href={`/jobs/${encodeURIComponent(job.job_id)}`}
                className="inline-flex items-center gap-1 text-xs text-rose-300 hover:text-rose-100 font-semibold self-start sm:self-auto shrink-0"
              >
                Inspect Block <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          ))}

          {/* Stale PRs */}
          {staleJobs.map((job) => (
            <div
              key={job.job_id}
              className="p-3.5 rounded-md border border-amber-900/60 bg-amber-950/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
              data-testid={`attention-stale-${job.job_id}`}
            >
              <div className="flex items-start sm:items-center gap-3">
                <span className="w-2 h-2 rounded-full bg-amber-400 shrink-0 mt-1 sm:mt-0" />
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-bold text-amber-200">
                      STALE EVIDENCE: {job.repository}
                    </span>
                    <span className="px-1.5 py-0.2 rounded bg-amber-950 text-amber-300 border border-amber-800 text-[10px] font-bold">
                      RE-VERIFICATION REQUIRED
                    </span>
                  </div>
                  <p className="text-zinc-300 text-[11px] mt-0.5">
                    Target branch head commit moved. Cryptographic proof must be re-evaluated.
                  </p>
                </div>
              </div>

              <Link
                href={`/jobs/${encodeURIComponent(job.job_id)}`}
                className="inline-flex items-center gap-1 text-xs text-amber-300 hover:text-amber-100 font-semibold self-start sm:self-auto shrink-0"
              >
                Re-Verify <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          ))}

          {/* Active Remediation Jobs */}
          {activeJobs.map((job) => (
            <div
              key={job.job_id}
              className="p-3.5 rounded-md border border-border-subtle bg-zinc-900/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
              data-testid={`attention-active-${job.job_id}`}
            >
              <div className="flex items-start sm:items-center gap-3">
                <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse shrink-0 mt-1 sm:mt-0" />
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-bold text-zinc-100">
                      ACTIVE VERIFICATION: {job.repository}
                    </span>
                    <span className="px-1.5 py-0.2 rounded bg-zinc-800 text-zinc-300 border border-zinc-700 text-[10px] font-bold uppercase">
                      {job.state || "RUNNING"}
                    </span>
                  </div>
                  <p className="text-zinc-400 text-[11px] mt-0.5">
                    Running AST patch checks in isolated gVisor container with 0 network egress.
                  </p>
                </div>
              </div>

              <Link
                href={`/jobs/${encodeURIComponent(job.job_id)}`}
                className="inline-flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 font-semibold self-start sm:self-auto shrink-0"
              >
                Live Telemetry <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
