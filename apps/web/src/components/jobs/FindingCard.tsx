"use client";

import React from "react";
import { TargetFindingInfo } from "@/lib/types";

interface FindingCardProps {
  finding?: TargetFindingInfo | null;
  defaultFingerprint?: string;
}

export function FindingCard({ finding, defaultFingerprint }: FindingCardProps) {
  const ruleId = finding?.rule_id || "python.sql-injection";
  const severity = finding?.severity || "HIGH";
  const fingerprint = finding?.fingerprint || defaultFingerprint || "—";
  const file = finding?.file;
  const line = finding?.line;
  const scanner = finding?.scanner || "Semgrep SAST";
  const description = finding?.description || `Automated detection for security rule ${ruleId}`;

  return (
    <div className="border border-border-subtle bg-surface-300 rounded-lg p-5 space-y-3" data-testid="finding-card">
      <div className="flex items-start justify-between gap-3 pb-3 border-b border-border-subtle">
        <div>
          <div className="text-[11px] font-mono uppercase tracking-wider text-zinc-500">
            Detected Finding · {scanner}
          </div>
          <h3 className="text-sm font-semibold text-zinc-100 font-mono mt-0.5 break-all">
            {ruleId}
          </h3>
        </div>
        <span className="px-2 py-0.2 rounded bg-amber-950/60 text-amber-300 text-[10px] font-mono border border-amber-800 uppercase font-semibold">
          {severity}
        </span>
      </div>

      <p className="text-xs text-zinc-300 leading-relaxed bg-zinc-900/60 p-2.5 rounded border border-zinc-800">
        {description}
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
        <div className="p-2.5 bg-zinc-900/40 rounded border border-zinc-800">
          <div className="text-[10px] text-zinc-500 uppercase">Target File</div>
          <div className="text-zinc-300 mt-0.5 truncate">
            {file ? `${file}${line ? `:${line}` : ""}` : "Source repository file"}
          </div>
        </div>

        <div className="p-2.5 bg-zinc-900/40 rounded border border-zinc-800">
          <div className="text-[10px] text-zinc-500 uppercase">Fingerprint</div>
          <div className="text-zinc-300 mt-0.5 truncate" title={fingerprint}>
            {fingerprint}
          </div>
        </div>
      </div>

      {finding?.code_context && (
        <div className="space-y-1">
          <div className="text-[10px] font-mono uppercase text-zinc-500">Code Context:</div>
          <pre className="p-2.5 bg-zinc-950 text-zinc-300 font-mono text-xs rounded border border-zinc-800 overflow-x-auto">
            <code>{finding.code_context}</code>
          </pre>
        </div>
      )}
    </div>
  );
}
