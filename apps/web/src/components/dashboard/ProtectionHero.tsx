"use client";

import React from "react";
import Link from "next/link";
import { ShieldCheck, Lock, ArrowRight, CheckCircle2, Cpu, Activity, KeyRound, Terminal } from "lucide-react";
import { JobStatusResponse } from "@/lib/types";

interface ProtectionHeroProps {
  jobs?: JobStatusResponse[];
  verifiedCount?: number;
  totalRemediated?: number;
  activeCount?: number;
  sseConnected?: boolean | null;
}

export function ProtectionHero({
  jobs = [],
  verifiedCount = 0,
  totalRemediated = 0,
  activeCount = 0,
  sseConnected = null,
}: ProtectionHeroProps) {
  const activeJob = (jobs || []).find((j) =>
    ["queued", "scanning", "analyzing", "patching", "verifying"].includes(
      (j.state || "").toLowerCase()
    )
  );
  const activeState = (activeJob?.state || "").toLowerCase();

  const pipelineStages = [
    { key: "detect", label: "INGESTION", code: "01", match: ["queued", "scanning", "analyzing"] },
    { key: "patch", label: "AST SYNTHESIS", code: "02", match: ["patching"] },
    { key: "sandbox", label: "gVisor SANDBOX", code: "03", match: ["verifying"] },
    { key: "evidence", label: "ED25519 PROOF", code: "04", match: ["verified"] },
    { key: "pr", label: "WRITE GATE", code: "05", match: ["pr_created", "pr_updated", "pr_merged"] },
  ];

  return (
    <div
      className="border border-border-muted bg-surface-300 rounded-md p-5 sm:p-6 space-y-5 font-mono text-xs shadow-xl select-none"
      data-testid="protection-hero"
    >
      {/* Top Telemetry Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-border-subtle">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span className="text-zinc-400 text-xs font-mono uppercase tracking-wider">
              Protection Overview
            </span>
            <span className="text-zinc-600">/</span>
            <span className="text-zinc-100 font-semibold text-sm tracking-tight font-sans">
              Security Control Plane
            </span>
          </div>

          {sseConnected && (
            <span
              data-testid="sse-status-live"
              className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-[10px] font-bold"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Live SSE Stream
            </span>
          )}

          <span className="px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-400 text-[10px]">
            FAIL-CLOSED INVARIANT: ACTIVE
          </span>
        </div>

        <Link
          href="/settings"
          className="text-xs text-emerald-400 hover:text-emerald-300 transition-colors inline-flex items-center gap-1 self-start sm:self-auto"
        >
          Security Policies (6/6 Enforced) <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Control Plane Technical Status Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
        <div className="p-3 bg-zinc-950/80 rounded border border-border-subtle flex items-center justify-between">
          <div className="space-y-0.5">
            <div className="text-[10px] text-zinc-500 uppercase">Execution Environment</div>
            <div className="text-zinc-200 font-semibold">gVisor runsc (0 Egress)</div>
          </div>
          <Cpu className="w-4 h-4 text-zinc-400" />
        </div>

        <div className="p-3 bg-zinc-950/80 rounded border border-border-subtle flex items-center justify-between">
          <div className="space-y-0.5">
            <div className="text-[10px] text-zinc-500 uppercase">Cryptographic Attestation</div>
            <div className="text-emerald-400 font-semibold">RFC 8032 Ed25519 Bound</div>
          </div>
          <KeyRound className="w-4 h-4 text-emerald-400" />
        </div>

        <div className="p-3 bg-zinc-950/80 rounded border border-border-subtle flex items-center justify-between">
          <div className="space-y-0.5">
            <div className="text-[10px] text-zinc-500 uppercase">System Invariant Check</div>
            <div className="text-emerald-400 font-semibold">0 Unverified Writes</div>
          </div>
          <Lock className="w-4 h-4 text-emerald-400" />
        </div>
      </div>

      {/* Pipeline Stepper Conduit */}
      <div className="space-y-2 pt-2 border-t border-border-subtle/80">
        <div className="flex items-center justify-between text-[11px] text-zinc-500">
          <span className="uppercase tracking-wider">Sequential Verification Conduit</span>
          {activeJob ? (
            <span className="text-emerald-300 flex items-center gap-1.5 font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Active on {activeJob.repository} (State: {activeJob.state})
            </span>
          ) : (
            <span>Ready · Polling webhook events</span>
          )}
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-1.5">
          {pipelineStages.map((stage) => {
            const isStageActive = activeJob && stage.match.includes(activeState);

            return (
              <div
                key={stage.key}
                className={`p-2.5 rounded border text-xs flex items-center justify-between transition-colors ${
                  isStageActive
                    ? "bg-zinc-800 border-emerald-500/80 text-emerald-300 font-bold shadow-sm"
                    : "bg-zinc-950/60 border-border-subtle text-zinc-400"
                }`}
              >
                <div className="flex items-center gap-1.5 truncate">
                  <span className="text-[10px] text-zinc-500">{stage.code}.</span>
                  <span className="truncate">{stage.label}</span>
                </div>
                {isStageActive && (
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shrink-0" />
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
