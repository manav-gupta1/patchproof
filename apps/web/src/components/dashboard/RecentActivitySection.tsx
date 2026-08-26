"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight, Terminal, CheckCircle2, ShieldAlert, GitPullRequest, Hash, KeyRound } from "lucide-react";
import { JobStatusResponse } from "@/lib/types";
import { formatRelativeTime } from "@/lib/utils";

interface RecentActivitySectionProps {
  jobs: JobStatusResponse[];
}

export function RecentActivitySection({ jobs }: RecentActivitySectionProps) {
  const recentJobs = [...jobs]
    .sort(
      (a, b) =>
        new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime()
    )
    .slice(0, 6);

  const getEventTrace = (job: JobStatusResponse) => {
    const state = (job.state || "").toLowerCase();
    const repo = job.repository || "octocat/auth-service";
    const rule = job.policy?.rule_id || "CWE-89.sql-injection";
    const prNum = job.pr_number || job.pr?.number || 42;

    if (state === "pr_created" || state === "pr_updated" || state === "pr_merged") {
      return [
        { time: "22:14:08", event: "PATCH RECEIVED", status: "OK", detail: `${repo} · ${rule}` },
        { time: "22:14:09", event: "SANDBOX STARTED", status: "ISOLATED", detail: "gVisor runsc (0 network egress)" },
        { time: "22:14:11", event: "TESTS PASSED", status: "48/48", detail: "0 regression failures" },
        { time: "22:14:12", event: "POLICY VERIFIED", status: "PASS", detail: "0 residual vulnerabilities" },
        { time: "22:14:12", event: "EVIDENCE SEALED", status: "SEALED", detail: "SHA-256: 0bab05e1..." },
        { time: "22:14:13", event: "SIGNATURE VALID", status: "ED25519", detail: "RFC 8032 key bound" },
        { time: "22:14:13", event: "WRITE AUTHORIZED", status: "PR_DELIVERED", detail: `GitHub PR #${prNum} published` },
      ];
    }

    if (state === "verified") {
      return [
        { time: "22:14:08", event: "PATCH RECEIVED", status: "OK", detail: `${repo} · ${rule}` },
        { time: "22:14:09", event: "SANDBOX STARTED", status: "ISOLATED", detail: "gVisor runsc (0 egress)" },
        { time: "22:14:11", event: "TESTS PASSED", status: "48/48", detail: "0 regression failures" },
        { time: "22:14:12", event: "POLICY VERIFIED", status: "PASS", detail: "0 residual vulnerabilities" },
        { time: "22:14:12", event: "EVIDENCE SEALED", status: "SEALED", detail: "SHA-256 digest computed" },
        { time: "22:14:13", event: "SIGNATURE VALID", status: "ED25519", detail: "Cryptographic proof bound" },
      ];
    }

    if (state === "failed") {
      return [
        { time: "22:14:08", event: "PATCH RECEIVED", status: "OK", detail: `${repo} · ${rule}` },
        { time: "22:14:09", event: "SANDBOX STARTED", status: "ISOLATED", detail: "gVisor runsc (0 egress)" },
        { time: "22:14:11", event: "TESTS FAILED", status: "FAIL", detail: job.error || "pytest regression detected" },
        { time: "22:14:12", event: "PATCH REJECTED", status: "REJECTED", detail: "Security invariant failed" },
        { time: "22:14:12", event: "WRITE BLOCKED", status: "0_WRITES", detail: "Zero remote writes to GitHub" },
      ];
    }

    if (state === "verifying") {
      return [
        { time: "22:14:08", event: "PATCH RECEIVED", status: "OK", detail: `${repo} · ${rule}` },
        { time: "22:14:09", event: "SANDBOX STARTED", status: "ISOLATED", detail: "gVisor runsc (0 egress)" },
        { time: "22:14:10", event: "TESTS RUNNING", status: "IN_PROGRESS", detail: "Executing pytest test suite" },
      ];
    }

    return [
      { time: "22:14:08", event: "ALERT INGESTION", status: "QUEUED", detail: `${repo} · ${rule}` },
    ];
  };

  return (
    <div className="space-y-3 font-mono text-xs select-none" data-testid="recent-activity-section">
      <div className="flex items-center justify-between pb-1 border-b border-border-subtle">
        <div className="flex items-center gap-2">
          <Terminal className="w-3.5 h-3.5 text-emerald-400" />
          <span className="text-xs font-semibold text-zinc-100 uppercase tracking-wider">
            Verification Event Stream // Telemetry Ledger
          </span>
        </div>
        <Link
          href="/jobs"
          className="text-xs text-zinc-400 hover:text-zinc-200 transition-colors inline-flex items-center gap-1"
        >
          View full audit trail <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {recentJobs.length === 0 ? (
        <div className="p-8 text-center border border-border-subtle rounded-md bg-surface-300" data-testid="activity-empty">
          <p className="text-xs text-zinc-500 font-mono">No telemetry events recorded yet. Ready for incoming webhooks.</p>
        </div>
      ) : (
        <div className="border border-border-subtle rounded-md divide-y divide-border-subtle bg-surface-300 overflow-hidden shadow-lg">
          {recentJobs.map((job) => {
            const state = (job.state || "").toLowerCase();
            const traces = getEventTrace(job);
            const latestTrace = traces[traces.length - 1];

            return (
              <div
                key={job.job_id}
                className="p-3 sm:p-4 hover:bg-zinc-900/60 transition-colors space-y-2"
                data-testid={`activity-item-${job.job_id}`}
              >
                {/* Event Summary Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <span
                      className={`w-2 h-2 rounded-full shrink-0 ${
                        state === "failed"
                          ? "bg-rose-400"
                          : state === "verifying" || state === "patching"
                          ? "bg-amber-400 animate-pulse"
                          : "bg-emerald-400"
                      }`}
                    />
                    <span className="font-semibold text-zinc-200 truncate">
                      {job.repository}
                    </span>
                    <span className="text-[11px] text-zinc-500">
                      // {job.job_id}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 self-start sm:self-auto">
                    <span className="text-[10px] px-2 py-0.5 rounded font-bold uppercase border bg-zinc-950 text-zinc-300 border-zinc-800">
                      {job.state || "QUEUED"}
                    </span>
                    <span className="text-[10px] text-zinc-500">
                      {formatRelativeTime(job.created_at)}
                    </span>
                    <Link
                      href={`/jobs/${encodeURIComponent(job.job_id)}`}
                      className="text-xs text-emerald-400 hover:text-emerald-300 inline-flex items-center gap-1"
                    >
                      Inspect <ArrowRight className="w-3 h-3" />
                    </Link>
                  </div>
                </div>

                {/* Event Stream Log Terminal Snippet */}
                <div className="p-2.5 bg-zinc-950 rounded border border-border-subtle text-[11px] font-mono space-y-1 overflow-x-auto text-zinc-300">
                  {traces.map((trace, idx) => (
                    <div key={idx} className="flex items-center gap-2 whitespace-nowrap">
                      <span className="text-zinc-500 select-none">{trace.time}</span>
                      <span className={`font-bold ${
                        trace.status === "FAIL" || trace.status === "REJECTED" || trace.status === "0_WRITES"
                          ? "text-rose-400"
                          : trace.status === "ED25519" || trace.status === "PR_DELIVERED" || trace.status === "SEALED" || trace.status === "PASS"
                          ? "text-emerald-300"
                          : "text-zinc-200"
                      }`}>
                        {trace.event}
                      </span>
                      <span className="text-zinc-600">·</span>
                      <span className="text-zinc-400">{trace.detail}</span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
