"use client";

import React from "react";
import { ExternalLink } from "lucide-react";
import { JobStatusResponse } from "@/lib/types";
import { formatSha } from "@/lib/utils";
import { isSafeGitHubUrl } from "@/lib/api";

interface GitHubCardProps {
  job: JobStatusResponse;
}

export function GitHubCard({ job }: GitHubCardProps) {
  const pr = job.pr;
  const prNumber = job.pr_number || pr?.number;
  const prUrl = job.pr_url || pr?.url;
  const branch = job.remediation_branch || pr?.branch || "patchproof/automated-fix";
  const baseBranch = pr?.base_branch || job.target_branch || "main";
  const commitSha = job.commit_sha;
  const isMerged = job.state === "pr_merged" || Boolean(job.merge_commit_sha);
  const isValidPrUrl = isSafeGitHubUrl(prUrl);

  return (
    <div className="border border-border-subtle bg-surface-300 rounded-lg p-5 space-y-4" data-testid="github-card">
      <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-3 pb-3 border-b border-border-subtle">
        <div>
          <div className="text-[11px] font-mono uppercase tracking-wider text-zinc-500">
            GitHub Delivery
          </div>
          <h3 className="text-sm font-semibold text-zinc-100 font-sans mt-0.5">
            Pull Request Publication Status
          </h3>
          <p className="text-xs text-zinc-400 mt-0.5">
            {prNumber ? `Remediation PR #${prNumber} generated and bound to evidence` : "Pull request published upon verified gate passage"}
          </p>
        </div>

        {isValidPrUrl && prUrl && (
          <a
            href={prUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-1.5 bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-mono font-semibold rounded inline-flex items-center gap-1.5 transition-colors self-start sm:self-auto"
            data-testid="open-pr-button"
          >
            Open Pull Request
            <ExternalLink className="w-3 h-3" />
          </a>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2 text-xs font-mono">
        <div className="p-2.5 bg-zinc-900/40 rounded border border-zinc-800">
          <div className="text-[10px] text-zinc-500 uppercase">Remediation Branch</div>
          <div className="text-zinc-200 mt-0.5 truncate" title={branch}>
            {branch}
          </div>
        </div>

        <div className="p-2.5 bg-zinc-900/40 rounded border border-zinc-800">
          <div className="text-[10px] text-zinc-500 uppercase">Base Branch</div>
          <div className="text-zinc-200 mt-0.5">{baseBranch}</div>
        </div>

        <div className="p-2.5 bg-zinc-900/40 rounded border border-zinc-800">
          <div className="text-[10px] text-zinc-500 uppercase">Target Commit SHA</div>
          <div className="text-zinc-200 mt-0.5 truncate" title={commitSha}>
            {formatSha(commitSha, 8)}
          </div>
        </div>

        <div className="p-2.5 bg-zinc-900/40 rounded border border-zinc-800">
          <div className="text-[10px] text-zinc-500 uppercase">PR Status</div>
          <div className="text-emerald-400 mt-0.5">
            {isMerged ? "MERGED" : prNumber ? `OPEN (#${prNumber})` : "NOT CREATED"}
          </div>
        </div>
      </div>
    </div>
  );
}
