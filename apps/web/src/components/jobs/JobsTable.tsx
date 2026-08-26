"use client";

import React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { JobStatusResponse } from "@/lib/types";
import { formatSha, formatRelativeTime } from "@/lib/utils";
import { isSafeGitHubUrl } from "@/lib/api";
import { GitPullRequest, ExternalLink, ArrowRight } from "lucide-react";

interface JobsTableProps {
  jobs: JobStatusResponse[];
  loading?: boolean;
}

export function JobsTable({ jobs, loading }: JobsTableProps) {
  const router = useRouter();

  if (loading) {
    return (
      <div className="animate-pulse space-y-1 p-4" data-testid="loading-spinner">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-10 bg-zinc-900 rounded" />
        ))}
      </div>
    );
  }

  const handleRowKeyDown = (e: React.KeyboardEvent, jobId: string) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      router.push(`/jobs/${encodeURIComponent(jobId)}`);
    }
  };

  const getStatusDisplay = (job: JobStatusResponse) => {
    const state = (job.state || "").toLowerCase();
    switch (state) {
      case "verified":
        return {
          dotClass: "bg-emerald-400",
          label: "VERIFIED",
        };
      case "pr_created":
      case "pr_updated":
      case "pr_merged":
        return {
          dotClass: "bg-emerald-400",
          label: "PR CREATED",
        };
      case "failed":
        return {
          dotClass: "bg-rose-400",
          label: "FAILED",
        };
      case "verifying":
        return {
          dotClass: "bg-indigo-400 animate-pulse",
          label: "VERIFYING",
        };
      case "patching":
        return {
          dotClass: "bg-amber-400 animate-pulse",
          label: "PATCHING",
        };
      case "analyzing":
      case "scanning":
      case "queued":
        return {
          dotClass: "bg-zinc-400",
          label: state.toUpperCase(),
        };
      default:
        return {
          dotClass: "bg-zinc-500",
          label: state.toUpperCase(),
        };
    }
  };

  return (
    <div className="overflow-x-auto" data-testid="jobs-table">
      <table className="w-full text-left text-xs border-collapse" aria-label="Remediation Jobs Table">
        <thead className="bg-surface-400 text-zinc-400 font-mono uppercase text-[10px] border-b border-border-subtle select-none">
          <tr>
            <th scope="col" className="py-2.5 px-3 font-medium">Status</th>
            <th scope="col" className="py-2.5 px-3 font-medium">Repository</th>
            <th scope="col" className="py-2.5 px-3 font-medium">Finding / Rule</th>
            <th scope="col" className="py-2.5 px-3 font-medium">Severity</th>
            <th scope="col" className="py-2.5 px-3 font-medium">Result / PR</th>
            <th scope="col" className="py-2.5 px-3 font-medium">Started</th>
            <th scope="col" className="py-2.5 px-3 font-medium text-right">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border-subtle font-normal text-zinc-300">
          {jobs.map((job) => {
            const pr = job.pr;
            const prNumber = job.pr_number || pr?.number;
            const prUrl = job.pr_url || pr?.url;
            const isValidPrUrl = isSafeGitHubUrl(prUrl);
            const status = getStatusDisplay(job);
            const ruleId = job.policy?.rule_id || "Vulnerability";
            const severity = job.policy?.severity || "high";

            return (
              <tr
                key={job.job_id}
                tabIndex={0}
                onKeyDown={(e) => handleRowKeyDown(e, job.job_id)}
                onClick={() => router.push(`/jobs/${encodeURIComponent(job.job_id)}`)}
                className="hover:bg-zinc-900/60 transition-colors group cursor-pointer focus:outline-none focus-visible:bg-zinc-900/80"
                data-testid={`job-row-${job.job_id}`}
                aria-label={`Job ${job.job_id} for ${job.repository}`}
              >
                {/* Status dot + label */}
                <td className="py-2.5 px-3 whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${status.dotClass}`} />
                    <span className="font-mono text-zinc-200 text-xs">{status.label}</span>
                  </div>
                </td>

                {/* Repository & Commit */}
                <td className="py-2.5 px-3 font-mono font-medium text-zinc-100 whitespace-nowrap">
                  <div className="flex items-center gap-1.5">
                    <span className="group-hover:text-white transition-colors">{job.repository}</span>
                    <span className="text-zinc-500 text-[11px]">@{formatSha(job.commit_sha, 7)}</span>
                  </div>
                </td>

                {/* Finding / Rule */}
                <td className="py-2.5 px-3 font-mono text-zinc-300 whitespace-nowrap">
                  <span className="truncate max-w-[200px] block" title={ruleId}>
                    {ruleId}
                  </span>
                </td>

                {/* Severity */}
                <td className="py-2.5 px-3 whitespace-nowrap font-mono text-[10px] uppercase">
                  <span
                    className={`px-1.5 py-0.2 rounded border ${
                      severity === "critical"
                        ? "bg-rose-950/60 text-rose-300 border-rose-800/80 font-semibold"
                        : severity === "high"
                        ? "bg-amber-950/60 text-amber-300 border-amber-800/80"
                        : "bg-zinc-800 text-zinc-300 border-zinc-700"
                    }`}
                  >
                    {severity}
                  </span>
                </td>

                {/* Result / PR */}
                <td className="py-2.5 px-3 whitespace-nowrap font-mono">
                  {prNumber && isValidPrUrl && prUrl ? (
                    <a
                      href={prUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-zinc-300 hover:text-white transition-colors underline-offset-2 hover:underline"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <GitPullRequest className="w-3 h-3 text-zinc-400" />
                      #{prNumber}
                      <ExternalLink className="w-2.5 h-2.5 opacity-60" />
                    </a>
                  ) : (job.state || "").toLowerCase() === "failed" ? (
                    <span className="text-rose-400 text-[11px]">0 writes (blocked)</span>
                  ) : (
                    <span className="text-zinc-600">—</span>
                  )}
                </td>

                {/* Started / Relative Time */}
                <td className="py-2.5 px-3 whitespace-nowrap font-mono text-zinc-500 text-[11px]" title={job.created_at || ""}>
                  {formatRelativeTime(job.created_at)}
                </td>

                {/* Action Link */}
                <td className="py-2.5 px-3 text-right whitespace-nowrap">
                  <Link
                    href={`/jobs/${encodeURIComponent(job.job_id)}`}
                    className="text-xs font-mono text-zinc-400 hover:text-zinc-100 transition-colors inline-flex items-center gap-1"
                    onClick={(e) => e.stopPropagation()}
                  >
                    Review <ArrowRight className="w-3 h-3" />
                  </Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
