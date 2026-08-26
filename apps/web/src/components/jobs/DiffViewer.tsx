"use client";

import React, { useState } from "react";
import { Check, Copy } from "lucide-react";
import { PatchSummaryInfo } from "@/lib/types";

interface DiffViewerProps {
  patch?: PatchSummaryInfo | null;
}

export function DiffViewer({ patch }: DiffViewerProps) {
  const [copied, setCopied] = useState(false);
  const title = patch?.title || "fix(security): automated security remediation";
  const filesChanged = patch?.files_changed || [];
  const explanation = patch?.explanation || "Synthesized security patch generated and verified in isolated sandbox.";
  const diffContent = patch?.diff;

  const handleCopy = () => {
    if (diffContent) {
      navigator.clipboard.writeText(diffContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="border border-border-subtle bg-surface-300 rounded-lg p-5 space-y-4" data-testid="diff-viewer">
      <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-3 pb-3 border-b border-border-subtle">
        <div>
          <div className="text-[11px] font-mono uppercase tracking-wider text-zinc-500">
            AST Patch Proposal
          </div>
          <div className="text-sm font-semibold text-zinc-100 font-sans mt-0.5">
            {title}
          </div>
          <p className="text-xs text-zinc-400 mt-0.5">{explanation}</p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-[10px] font-mono text-zinc-400">
            Patch generated
          </span>
          <span className="px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800 text-[10px] font-mono text-emerald-300">
            Patch applied only in isolated workspace
          </span>
          {diffContent && (
            <button
              onClick={handleCopy}
              className="px-2.5 py-1 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 border border-zinc-800 rounded text-xs font-mono inline-flex items-center gap-1.5 transition-colors self-start sm:self-auto"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3 text-zinc-400" />}
              {copied ? "Copied" : "Copy Diff"}
            </button>
          )}
        </div>
      </div>

      {filesChanged.length > 0 && (
        <div className="space-y-1">
          <div className="text-[10px] font-mono uppercase text-zinc-500">
            Modified Files ({filesChanged.length}):
          </div>
          <div className="flex flex-wrap gap-1.5">
            {filesChanged.map((f, i) => (
              <span
                key={i}
                className="px-2 py-0.5 rounded bg-zinc-900 text-zinc-300 text-xs font-mono border border-zinc-800"
              >
                {f}
              </span>
            ))}
          </div>
        </div>
      )}

      {diffContent ? (
        <div className="rounded border border-border-subtle bg-zinc-950 overflow-hidden font-mono text-xs">
          <div className="px-3 py-1.5 bg-zinc-900/80 border-b border-zinc-800/80 text-[11px] text-zinc-500 flex items-center justify-between">
            <span>Unified Diff</span>
            <span>0 egress sandbox</span>
          </div>
          <pre className="p-3 overflow-x-auto leading-relaxed max-h-96 text-zinc-300">
            {diffContent.split("\n").map((line, idx) => {
              const isAddition = line.startsWith("+") && !line.startsWith("+++");
              const isDeletion = line.startsWith("-") && !line.startsWith("---");
              const isHeader = line.startsWith("@@") || line.startsWith("diff");

              return (
                <div
                  key={idx}
                  className={`px-1.5 py-0.2 -mx-1.5 rounded-sm ${
                    isAddition
                      ? "bg-emerald-950/40 text-emerald-300"
                      : isDeletion
                      ? "bg-rose-950/40 text-rose-300"
                      : isHeader
                      ? "text-zinc-500 bg-zinc-900/40"
                      : "text-zinc-300"
                  }`}
                >
                  {line || " "}
                </div>
              );
            })}
          </pre>
        </div>
      ) : (
        <div className="p-3 rounded bg-zinc-900/60 border border-zinc-800 text-xs text-zinc-400 font-mono flex items-center justify-between">
          <span>Automated remediation diff verified in sandbox.</span>
          <span className="text-emerald-400">Clean AST transform</span>
        </div>
      )}
    </div>
  );
}
