"use client";

import React from "react";
import { PolicyDecision } from "@/lib/types";

interface PolicyCardProps {
  policy?: PolicyDecision | null;
}

export function PolicyCard({ policy }: PolicyCardProps) {
  const isAllowed = policy?.allowed !== false;
  const action = policy?.action || (isAllowed ? "remediate_and_publish" : "blocked_by_policy");
  const reason = policy?.reason || (isAllowed ? "Target vulnerability exceeds minimum severity threshold." : "Remediation did not satisfy security policy rules.");
  const policySource = policy?.policy_source || "repository default";

  return (
    <div className="border border-border-subtle bg-surface-300 rounded-lg p-5 space-y-3" data-testid="policy-card">
      <div className="flex items-start justify-between gap-3 pb-3 border-b border-border-subtle">
        <div>
          <div className="text-[11px] font-mono uppercase tracking-wider text-zinc-500">
            Repository Policy Evaluation
          </div>
          <h3 className="text-sm font-semibold text-zinc-100 font-sans mt-0.5">
            Remediation Decision
          </h3>
        </div>
        <span
          className={`px-2 py-0.2 rounded text-[10px] font-mono font-semibold uppercase ${
            isAllowed
              ? "bg-emerald-950/60 text-emerald-300 border border-emerald-800"
              : "bg-rose-950/60 text-rose-300 border border-rose-800"
          }`}
        >
          {isAllowed ? "✓ ALLOWED" : "✕ BLOCKED"}
        </span>
      </div>

      <p className="text-xs text-zinc-300 leading-relaxed bg-zinc-900/60 p-2.5 rounded border border-zinc-800">
        {reason}
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs font-mono">
        <div className="p-2.5 bg-zinc-900/40 rounded border border-zinc-800">
          <div className="text-[10px] text-zinc-500 uppercase">Policy Action</div>
          <div className="text-zinc-200 mt-0.5">{action}</div>
        </div>

        <div className="p-2.5 bg-zinc-900/40 rounded border border-zinc-800">
          <div className="text-[10px] text-zinc-500 uppercase">Auto-Create PR</div>
          <div className="text-emerald-400 mt-0.5">
            {policy?.auto_create_pr !== false ? "Enabled" : "Disabled"}
          </div>
        </div>

        <div className="p-2.5 bg-zinc-900/40 rounded border border-zinc-800">
          <div className="text-[10px] text-zinc-500 uppercase">Policy Source</div>
          <div className="text-zinc-200 mt-0.5 truncate">{policySource}</div>
        </div>
      </div>
    </div>
  );
}
