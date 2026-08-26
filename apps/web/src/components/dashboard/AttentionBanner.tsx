"use client";

import React from "react";
import Link from "next/link";
import { AlertCircle, Cpu, ArrowRight } from "lucide-react";
import { JobStatusResponse } from "@/lib/types";

interface AttentionBannerProps {
  jobs: JobStatusResponse[];
}

export function AttentionBanner({ jobs }: AttentionBannerProps) {
  const activeJobs = jobs.filter((j) =>
    ["queued", "scanning", "analyzing", "patching", "verifying"].includes(
      (j.state || "").toLowerCase()
    )
  );

  const failedJobs = jobs.filter(
    (j) => (j.state || "").toLowerCase() === "failed"
  );

  if (activeJobs.length === 0 && failedJobs.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3" data-testid="attention-banner-section">
      {/* Active Jobs Alert */}
      {activeJobs.length > 0 && (
        <div className="p-4 rounded-xl border border-indigo-800/60 bg-indigo-950/30 flex items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-3">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-400 animate-pulse" />
            <div>
              <span className="font-semibold text-white">
                {activeJobs.length} {activeJobs.length === 1 ? "Remediation" : "Remediations"} Currently Active
              </span>
              <p className="text-slate-400 text-[11px] mt-0.5">
                Executing patch synthesis & verification gates in isolated gVisor containers
              </p>
            </div>
          </div>
          <Link
            href="/jobs?state=verifying"
            className="inline-flex items-center gap-1 font-mono text-indigo-400 hover:text-indigo-300 font-semibold shrink-0"
          >
            View Active <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}

      {/* Failed Jobs Alert */}
      {failedJobs.length > 0 && (
        <div className="p-4 rounded-xl border border-rose-900/60 bg-rose-950/30 flex items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <div>
              <span className="font-semibold text-rose-200">
                {failedJobs.length} {failedJobs.length === 1 ? "Remediation Blocked" : "Remediations Blocked"} by Safety Policy
              </span>
              <p className="text-rose-300/80 text-[11px] mt-0.5">
                Verification checks failed in sandbox. PR publication was prevented to protect production code.
              </p>
            </div>
          </div>
          <Link
            href="/jobs?state=failed"
            className="inline-flex items-center gap-1 font-mono text-rose-400 hover:text-rose-300 font-semibold shrink-0"
          >
            Inspect Failures <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}
    </div>
  );
}
