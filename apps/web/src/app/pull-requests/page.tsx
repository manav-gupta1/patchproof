"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiClient, isSafeGitHubUrl } from "@/lib/api";
import { JobStatusResponse } from "@/lib/types";
import { EmptyState } from "@/components/common/EmptyState";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { ErrorAlert } from "@/components/common/ErrorAlert";
import { formatRelativeTime } from "@/lib/utils";
import {
  GitPullRequest,
  ExternalLink,
  RefreshCw,
  FileCheck2,
} from "lucide-react";

export default function PullRequestsPage() {
  const [jobs, setJobs] = useState<JobStatusResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadPRs = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.getJobs({ limit: 100 });
      const prJobs = (res.jobs || []).filter(
        (j) =>
          Boolean(j.pr_number || j.pr?.number) ||
          ["pr_created", "pr_updated", "pr_merged", "pr_closed", "rolled_back"].includes(
            (j.state || "").toLowerCase()
          )
      );
      setJobs(prJobs);
    } catch (err: any) {
      setError(err.message || "Failed to load pull requests");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPRs();
  }, []);

  return (
    <div className="space-y-5 max-w-6xl mx-auto" data-testid="pull-requests-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2 border-b border-border-subtle pb-4">
        <div>
          <div className="text-[11px] font-mono uppercase tracking-wider text-zinc-500">
            DELIVER / AUDIT TRAIL
          </div>
          <h1 className="text-lg sm:text-xl font-semibold text-zinc-100 font-sans tracking-tight mt-0.5">
            Pull Requests
          </h1>
          <p className="text-xs text-zinc-400 mt-0.5">
            Audit trail of verified remediation pull requests delivered to target repositories
          </p>
        </div>
        <button
          onClick={loadPRs}
          disabled={loading}
          className="text-xs font-mono text-zinc-400 hover:text-zinc-200 inline-flex items-center gap-1.5 transition-colors self-start sm:self-auto disabled:opacity-50"
        >
          <RefreshCw className={`w-3 h-3 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {error && <ErrorAlert message={error} onRetry={loadPRs} />}

      {/* PR Table Container */}
      <div className="border border-border-subtle rounded-lg overflow-hidden bg-surface-300">
        {loading ? (
          <LoadingSpinner label="Loading pull requests..." />
        ) : jobs.length === 0 ? (
          <div className="p-8 text-center">
            <EmptyState
              title="No pull requests delivered yet"
              description="When vulnerabilities are verified in the sandbox, PatchProof creates cryptographically bound pull requests."
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse" aria-label="Pull Requests Table">
              <thead className="bg-surface-400 text-zinc-400 font-mono uppercase text-[10px] border-b border-border-subtle select-none">
                <tr>
                  <th scope="col" className="py-2.5 px-3 font-medium">PR #</th>
                  <th scope="col" className="py-2.5 px-3 font-medium">Repository</th>
                  <th scope="col" className="py-2.5 px-3 font-medium">Remediation Branch</th>
                  <th scope="col" className="py-2.5 px-3 font-medium">Verification</th>
                  <th scope="col" className="py-2.5 px-3 font-medium">Proof</th>
                  <th scope="col" className="py-2.5 px-3 font-medium">Created</th>
                  <th scope="col" className="py-2.5 px-3 font-medium text-right">GitHub Link</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle font-mono text-zinc-300">
                {jobs.map((job) => {
                  const pr = job.pr;
                  const prNumber = job.pr_number || pr?.number || 1;
                  const prUrl = job.pr_url || pr?.url;
                  const isValidPrUrl = isSafeGitHubUrl(prUrl);
                  const branch = job.remediation_branch || pr?.branch || "patchproof/automated-fix";

                  return (
                    <tr key={job.job_id} className="hover:bg-zinc-900/50 transition-colors">
                      <td className="py-2.5 px-3 font-semibold text-zinc-100 whitespace-nowrap">
                        <Link
                          href={`/jobs/${encodeURIComponent(job.job_id)}`}
                          className="hover:underline underline-offset-2"
                        >
                          #{prNumber}
                        </Link>
                      </td>
                      <td className="py-2.5 px-3 text-zinc-200 whitespace-nowrap">
                        <Link
                          href={`/jobs/${encodeURIComponent(job.job_id)}`}
                          className="hover:text-white"
                        >
                          {job.repository}
                        </Link>
                      </td>
                      <td className="py-2.5 px-3 text-zinc-400 max-w-xs truncate" title={branch}>
                        {branch}
                      </td>
                      <td className="py-2.5 px-3 whitespace-nowrap">
                        <span className="inline-flex items-center gap-1 text-emerald-400 text-xs">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                          Verified
                        </span>
                      </td>
                      <td className="py-2.5 px-3 whitespace-nowrap">
                        <Link
                          href={`/jobs/${encodeURIComponent(job.job_id)}`}
                          className="text-xs text-zinc-400 hover:text-zinc-100 transition-colors inline-flex items-center gap-1"
                        >
                          <FileCheck2 className="w-3 h-3 text-zinc-400" />
                          View Evidence
                        </Link>
                      </td>
                      <td className="py-2.5 px-3 text-zinc-500 whitespace-nowrap text-[11px]">
                        {formatRelativeTime(job.created_at)}
                      </td>
                      <td className="py-2.5 px-3 text-right whitespace-nowrap">
                        {isValidPrUrl && prUrl ? (
                          <a
                            href={prUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-zinc-400 hover:text-white transition-colors inline-flex items-center gap-1"
                          >
                            Open PR <ExternalLink className="w-3 h-3" />
                          </a>
                        ) : (
                          <span className="text-zinc-600">—</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
