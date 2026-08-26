"use client";

import React from "react";
import { AlertOctagon, ShieldAlert, XCircle } from "lucide-react";

interface FailureBannerProps {
  error?: string | null;
  state?: string;
  invalidationReason?: string | null;
}

export function FailureBanner({
  error,
  state,
  invalidationReason,
}: FailureBannerProps) {
  const reasonText = error || invalidationReason || "Verification checks failed or security boundary was triggered.";

  return (
    <div
      className="bg-rose-950/30 border border-rose-800/80 rounded-md p-5 text-rose-100"
      data-testid="failure-banner"
      role="alert"
    >
      <div className="flex items-start gap-3.5">
        <div className="w-8 h-8 rounded bg-rose-950 border border-rose-800 flex items-center justify-center text-rose-400 shrink-0">
          <AlertOctagon className="w-4 h-4" />
        </div>

        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-bold text-rose-200 font-sans">Remediation failed</h3>
            <span className="px-2 py-0.2 rounded bg-rose-950 text-rose-300 text-[10px] font-mono uppercase font-bold border border-rose-800">
              Safety Guard Active
            </span>
          </div>

          <p className="text-xs text-rose-200/90 mt-1 font-sans">
            Verification did not pass.
          </p>

          <div className="mt-3 p-3 bg-zinc-950 rounded border border-rose-900/60 font-mono text-xs text-rose-300">
            <div className="text-[10px] uppercase text-zinc-500 font-bold mb-1">Diagnostic Reason:</div>
            <div className="break-all">{reasonText}</div>
          </div>

          <div className="mt-3 flex items-center gap-2 text-xs text-rose-300 font-medium bg-rose-950/40 px-3 py-2 rounded border border-rose-900/40">
            <ShieldAlert className="w-3.5 h-3.5 text-rose-400 shrink-0" />
            <span>PR publication was blocked because verification failed. No Pull Request was created.</span>
          </div>
        </div>
      </div>
    </div>
  );
}
