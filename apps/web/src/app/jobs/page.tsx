"use client";

import React, { useEffect, useState, useMemo } from "react";
import { apiClient } from "@/lib/api";
import { JobStatusResponse } from "@/lib/types";
import { JobsTable } from "@/components/jobs/JobsTable";
import { EmptyState } from "@/components/common/EmptyState";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { ErrorAlert } from "@/components/common/ErrorAlert";
import { Search, RefreshCw, GitFork } from "lucide-react";

type QuickFilter = "all" | "active" | "attention" | "verified" | "pr_created" | "failed";

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobStatusResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [quickFilter, setQuickFilter] = useState<QuickFilter>("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [repoFilter, setRepoFilter] = useState("");

  const loadJobs = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.getJobs({
        repository: repoFilter || undefined,
        limit: 100,
      });
      setJobs(res.jobs || []);
    } catch (err: any) {
      setError(err.message || "Failed to load jobs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadJobs();
  }, [repoFilter]);

  const repositories = useMemo(() => {
    const set = new Set<string>();
    jobs.forEach((j) => {
      if (j.repository) set.add(j.repository);
    });
    return Array.from(set).sort();
  }, [jobs]);

  const filteredJobs = useMemo(() => {
    return jobs.filter((job) => {
      const state = (job.state || "").toLowerCase();
      const isFailed = state === "failed";
      const isStale = Boolean(job.is_stale);
      const isActive = ["queued", "scanning", "analyzing", "patching", "verifying"].includes(state);
      const isVerified = ["verified", "pr_created", "pr_updated", "pr_merged"].includes(state);
      const isPrCreated = Boolean(
        job.pr_number ||
          job.pr?.number ||
          ["pr_created", "pr_updated", "pr_merged"].includes(state)
      );

      if (quickFilter === "active" && !isActive) return false;
      if (quickFilter === "attention" && !isFailed && !isStale) return false;
      if (quickFilter === "verified" && !isVerified) return false;
      if (quickFilter === "pr_created" && !isPrCreated) return false;
      if (quickFilter === "failed" && !isFailed) return false;

      if (!searchTerm.trim()) return true;
      const term = searchTerm.toLowerCase();
      return (
        job.job_id.toLowerCase().includes(term) ||
        job.repository.toLowerCase().includes(term) ||
        job.commit_sha.toLowerCase().includes(term) ||
        (job.policy?.rule_id && job.policy.rule_id.toLowerCase().includes(term)) ||
        (job.remediation_branch && job.remediation_branch.toLowerCase().includes(term)) ||
        (job.error && job.error.toLowerCase().includes(term))
      );
    });
  }, [jobs, quickFilter, searchTerm]);

  const activeCount = jobs.filter((j) =>
    ["queued", "scanning", "analyzing", "patching", "verifying"].includes(
      (j.state || "").toLowerCase()
    )
  ).length;

  const attentionCount = jobs.filter(
    (j) => (j.state || "").toLowerCase() === "failed" || Boolean(j.is_stale)
  ).length;

  return (
    <div className="space-y-6 max-w-7xl mx-auto" data-testid="jobs-page">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2 border-b border-border-subtle pb-4">
        <div>
          <div className="text-[11px] font-mono uppercase tracking-wider text-zinc-500">
            PROTECT / REMEDIATIONS
          </div>
          <h1 className="text-lg sm:text-xl font-semibold text-zinc-100 font-sans tracking-tight mt-0.5">
            Remediations
          </h1>
          <p className="text-xs text-zinc-400 mt-0.5">
            Security findings, AST patch proposals, sandbox verification logs, and delivered PRs
          </p>
        </div>
        <button
          onClick={loadJobs}
          disabled={loading}
          className="text-xs font-mono text-zinc-400 hover:text-zinc-200 inline-flex items-center gap-1.5 transition-colors self-start sm:self-auto disabled:opacity-50"
        >
          <RefreshCw className={`w-3 h-3 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {error && <ErrorAlert message={error} onRetry={loadJobs} />}

      {/* Filter and Search Bar */}
      <div className="space-y-2.5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          {/* Quick Filter Pills */}
          <div className="flex items-center gap-1 overflow-x-auto pb-1 sm:pb-0" role="tablist" aria-label="Remediation quick filters">
            <button
              onClick={() => setQuickFilter("all")}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-colors whitespace-nowrap ${
                quickFilter === "all"
                  ? "bg-zinc-800 text-zinc-100 font-medium"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900"
              }`}
            >
              All ({jobs.length})
            </button>
            <button
              onClick={() => setQuickFilter("attention")}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-colors whitespace-nowrap ${
                quickFilter === "attention"
                  ? "bg-zinc-800 text-rose-300 font-medium"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900"
              }`}
            >
              Attention ({attentionCount})
            </button>
            <button
              onClick={() => setQuickFilter("active")}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-colors whitespace-nowrap ${
                quickFilter === "active"
                  ? "bg-zinc-800 text-zinc-100 font-medium"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900"
              }`}
            >
              Active ({activeCount})
            </button>
            <button
              onClick={() => setQuickFilter("verified")}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-colors whitespace-nowrap ${
                quickFilter === "verified"
                  ? "bg-zinc-800 text-emerald-300 font-medium"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900"
              }`}
            >
              Verified
            </button>
            <button
              onClick={() => setQuickFilter("pr_created")}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-colors whitespace-nowrap ${
                quickFilter === "pr_created"
                  ? "bg-zinc-800 text-zinc-100 font-medium"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900"
              }`}
            >
              PR Created
            </button>
            <button
              onClick={() => setQuickFilter("failed")}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-colors whitespace-nowrap ${
                quickFilter === "failed"
                  ? "bg-zinc-800 text-rose-300 font-medium"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900"
              }`}
            >
              Blocked
            </button>
          </div>

          {/* Search Input */}
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-2.5 top-2.5 pointer-events-none" />
              <input
                type="text"
                placeholder="Search rule, repo, SHA..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full sm:w-64 pl-8 pr-3 py-1.5 bg-zinc-900 border border-zinc-800 rounded text-xs font-mono text-zinc-200 placeholder-zinc-500 focus:outline-none focus-visible:border-zinc-600 transition-colors"
                data-testid="jobs-search-input"
                aria-label="Search jobs"
              />
            </div>

            {repositories.length > 1 && (
              <div className="relative">
                <select
                  value={repoFilter}
                  onChange={(e) => setRepoFilter(e.target.value)}
                  className="pl-3 pr-8 py-1.5 bg-zinc-900 border border-zinc-800 rounded text-xs font-mono text-zinc-200 focus:outline-none focus-visible:border-zinc-600 transition-colors"
                  data-testid="jobs-repo-filter"
                  aria-label="Filter by repository"
                >
                  <option value="">All repositories</option>
                  {repositories.map((repo) => (
                    <option key={repo} value={repo}>
                      {repo}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </div>

        {/* Jobs Table Container */}
        <div className="border border-border-subtle rounded-lg overflow-hidden bg-surface-300">
          {loading ? (
            <LoadingSpinner label="Loading remediation workflows..." />
          ) : filteredJobs.length === 0 ? (
            <div className="p-8 text-center">
              <EmptyState
                title={
                  quickFilter === "attention"
                    ? "No attention required"
                    : searchTerm || repoFilter
                    ? "No matching workflows found"
                    : "No remediation activity yet"
                }
                description={
                  quickFilter === "attention"
                    ? "All active remediation workflows are passing security gates."
                    : searchTerm || repoFilter
                    ? "No remediation jobs match your search criteria."
                    : "Workflows will appear here when a security finding is detected."
                }
                action={
                  (searchTerm || repoFilter || quickFilter !== "all") && (
                    <button
                      onClick={() => {
                        setSearchTerm("");
                        setRepoFilter("");
                        setQuickFilter("all");
                      }}
                      className="px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-xs font-mono text-zinc-200 rounded transition-colors"
                    >
                      Reset Filters
                    </button>
                  )
                }
              />
            </div>
          ) : (
            <JobsTable jobs={filteredJobs} />
          )}
        </div>
      </div>
    </div>
  );
}
