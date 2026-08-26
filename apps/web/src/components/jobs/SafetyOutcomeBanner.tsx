"use client";

import React from "react";
import { GitMerge, AlertTriangle } from "lucide-react";
import { JobStatusResponse } from "@/lib/types";

interface SafetyOutcomeBannerProps {
  job: JobStatusResponse;
}

export function SafetyOutcomeBanner({ job }: SafetyOutcomeBannerProps) {
  const state = (job.state || "queued").toLowerCase();
  const isVerified = ["verified", "pr_created", "pr_updated", "pr_merged"].includes(state);
  const isFailed = state === "failed";
  const isMerged = state === "pr_merged" || Boolean(job.merge_commit_sha);
  const isStale = Boolean(job.is_stale);

  if (isMerged) {
    return (
      <div
        className="p-4 rounded-lg border border-purple-800/80 bg-purple-950/30 text-purple-100"
        data-testid="safety-banner-merged"
        role="region"
        aria-label="Safety outcome: Merged"
      >
        <div className="flex items-center gap-3">
          <GitMerge className="w-5 h-5 text-purple-400 shrink-0" />
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-purple-200">
                PR MERGED INTO TARGET BRANCH
              </h2>
              <span className="px-1.5 py-0.2 rounded bg-purple-900 text-purple-200 text-[10px] font-mono border border-purple-700">
                Complete
              </span>
            </div>
            <p className="text-xs text-purple-300 mt-0.5">
              The verified patch was merged into the target repository. Cryptographic proof remains bound to the merge commit.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (isStale) {
    return (
      <div
        className="p-4 rounded-lg border border-amber-800/80 bg-amber-950/30 text-amber-100"
        data-testid="safety-banner-stale"
        role="region"
        aria-label="Safety outcome: Stale"
      >
        <div className="flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold uppercase tracking-wider font-mono text-amber-200">
                EVIDENCE STALE — RE-VERIFICATION REQUIRED
              </h2>
              <span className="px-1.5 py-0.2 rounded bg-amber-900 text-amber-200 text-[10px] font-mono border border-amber-700">
                Head SHA Changed
              </span>
            </div>
            <p className="text-xs text-amber-300 mt-0.5">
              New commits were pushed to the target branch after verification. Prior evidence is invalidated for current head SHA.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (isVerified) {
    return (
      <div
        className="p-4 sm:p-5 rounded-lg border border-emerald-700/60 bg-emerald-950/20 text-emerald-100"
        data-testid="safety-banner-verified"
        role="region"
        aria-label="Safety outcome: Verified"
      >
        <div className="flex items-start gap-3.5">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shrink-0 mt-1" />
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-base font-bold uppercase tracking-wider font-mono text-emerald-300">
                VERIFIED → SAFE TO PUBLISH
              </h2>
              <span className="px-2 py-0.2 rounded bg-emerald-950 text-emerald-300 text-[10px] font-mono border border-emerald-800 font-semibold">
                Gates Passed
              </span>
            </div>
            <p className="text-xs text-emerald-200/90 leading-relaxed font-sans">
              Remediation patch successfully passed syntax AST validation, exploit elimination, and zero-regression security re-scans in the isolated gVisor sandbox. Cryptographic Ed25519 evidence is signed and bound to this verification.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (isFailed) {
    const reasonText = job.error || job.invalidation_reason || "Verification checks failed or security boundary was triggered.";
    return (
      <div
        className="p-4 sm:p-5 rounded-lg border border-rose-800/80 bg-rose-950/30 text-rose-100"
        data-testid="safety-banner-failed"
        role="region"
        aria-label="Safety outcome: Failed"
      >
        <div className="flex items-start gap-3.5">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-400 shrink-0 mt-1" />
          <div className="space-y-1.5 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-base font-bold uppercase tracking-wider font-mono text-rose-300">
                UNVERIFIED → ZERO GITHUB WRITES (PUBLICATION BLOCKED)
              </h2>
              <span className="px-2 py-0.2 rounded bg-rose-950 text-rose-300 text-[10px] font-mono border border-rose-800 font-semibold">
                Safety Invariant Active
              </span>
            </div>
            <p className="text-xs text-rose-200/90 leading-relaxed">
              Patch failed automated sandbox verification. In accordance with PatchProof safety invariants, GitHub publication was strictly prevented. Zero remote write operations occurred.
            </p>
            <div className="mt-2 p-2.5 bg-zinc-950 rounded border border-rose-900/60 font-mono text-[11px] text-rose-300 break-all">
              <span className="text-[10px] uppercase text-zinc-500 font-bold block mb-0.5">Diagnostic Reason:</span>
              {reasonText}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // In-Progress / Queued
  return (
    <div
      className="p-4 rounded-lg border border-zinc-800 bg-zinc-900/40 text-zinc-200"
      data-testid="safety-banner-inprogress"
      role="region"
      aria-label="Safety outcome: In Progress"
    >
      <div className="flex items-center gap-3">
        <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse shrink-0" />
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xs font-bold uppercase tracking-wider font-mono text-zinc-200">
              REMEDIATION IN PROGRESS
            </h2>
            <span className="px-1.5 py-0.2 rounded bg-zinc-800 text-zinc-300 text-[10px] font-mono border border-zinc-700">
              Isolated Sandbox
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-0.5">
            Running AST patch synthesis and sandbox verification checks in isolated container workspace.
          </p>
        </div>
      </div>
    </div>
  );
}
