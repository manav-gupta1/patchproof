"use client";

import React from "react";
import {
  ShieldAlert,
  Search,
  Code2,
  Cpu,
  FileCheck2,
  GitPullRequest,
  Check,
  X,
  Clock,
  Ban,
  ArrowRight,
  AlertTriangle,
  Lock,
  ShieldCheck,
} from "lucide-react";
import { JobStatusResponse, JobEvidenceResponse } from "@/lib/types";

interface VerificationJourneyPipelineProps {
  job: JobStatusResponse;
  evidence?: JobEvidenceResponse | null;
}

interface StageDefinition {
  id: string;
  stepNum: string;
  label: string;
  shortDesc: string;
  icon: React.ElementType;
}

const STAGES: StageDefinition[] = [
  {
    id: "detect",
    stepNum: "01",
    label: "DETECT",
    shortDesc: "Alert Ingested & Staged",
    icon: Search,
  },
  {
    id: "analyze",
    stepNum: "02",
    label: "ANALYZE",
    shortDesc: "AST Syntax & Context",
    icon: Code2,
  },
  {
    id: "patch",
    stepNum: "03",
    label: "PATCH",
    shortDesc: "Candidate Patch Applied",
    icon: FileCheck2,
  },
  {
    id: "verify",
    stepNum: "04",
    label: "VERIFY",
    shortDesc: "gVisor Sandbox & Tests",
    icon: Cpu,
  },
  {
    id: "proof",
    stepNum: "05",
    label: "PROOF",
    shortDesc: "Ed25519 Sealed Evidence",
    icon: ShieldAlert,
  },
  {
    id: "write",
    stepNum: "06",
    label: "AUTHORIZED WRITE",
    shortDesc: "GitHub PR Delivery",
    icon: GitPullRequest,
  },
];

export function VerificationJourneyPipeline({
  job,
  evidence,
}: VerificationJourneyPipelineProps) {
  const state = (job.state || "queued").toLowerCase();
  const isFailed = state === "failed";
  const isVerified = [
    "verified",
    "pr_created",
    "pr_updated",
    "pr_merged",
  ].includes(state);
  const events = job.events || [];
  const errorMsg = (job.error || "").toLowerCase();

  // Canonical stage progression index: 0..5
  let activeIndex = -1;
  let failedIndex = -1;

  if (state === "queued" || state === "scanning") {
    activeIndex = 0;
  } else if (state === "analyzing") {
    activeIndex = 1;
  } else if (state === "patching") {
    activeIndex = 2;
  } else if (state === "verifying") {
    activeIndex = 3;
  } else if (state === "verified") {
    activeIndex = 5;
  } else if (["pr_created", "pr_updated", "pr_merged"].includes(state)) {
    activeIndex = 6;
  } else if (isFailed) {
    const reachedStates = new Set(
      events.map((e) => (e.to_state || "").toLowerCase())
    );

    if (errorMsg.includes("policy") || (job.policy && !job.policy.allowed)) {
      failedIndex = 3;
    } else if (
      errorMsg.includes("sandbox") ||
      errorMsg.includes("gvisor") ||
      errorMsg.includes("test") ||
      errorMsg.includes("regression") ||
      reachedStates.has("verifying")
    ) {
      failedIndex = 3;
    } else if (
      errorMsg.includes("patch") ||
      errorMsg.includes("ast") ||
      errorMsg.includes("syntax") ||
      reachedStates.has("patching") ||
      reachedStates.has("analyzing")
    ) {
      failedIndex = 1;
    } else if (
      errorMsg.includes("github") ||
      errorMsg.includes("token") ||
      errorMsg.includes("pull request") ||
      reachedStates.has("verified")
    ) {
      failedIndex = 5;
    } else {
      failedIndex = 0;
    }
  }

  return (
    <div
      className="border border-border-subtle bg-surface-200 rounded-xl p-5 md:p-6 space-y-6 relative overflow-hidden shadow-xl"
      data-testid="verification-journey-pipeline"
    >
      {/* Header bar with strict status */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border-subtle/80 pb-4">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-widest text-zinc-500 font-semibold flex items-center gap-2">
            <span>Deterministic Verification Machine</span>
            <span>·</span>
            <span className="text-zinc-400">gVisor Sandbox Isolated</span>
          </div>
          <h3 className="text-base sm:text-lg font-bold text-zinc-100 font-mono mt-0.5 tracking-tight flex items-center gap-2">
            DETECT ──► ANALYZE ──► PATCH ──► VERIFY ──► PROOF ──► WRITE
          </h3>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          {isVerified ? (
            <span className="px-3 py-1 rounded-lg bg-emerald-950/80 border border-emerald-700/80 text-emerald-300 font-bold flex items-center gap-1.5 shadow-sm">
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              PATCH VERIFIED · ALL GATES PASSED
            </span>
          ) : isFailed ? (
            <span className="px-3 py-1 rounded-lg bg-rose-950/80 border border-rose-800 text-rose-300 font-bold flex items-center gap-1.5">
              <Ban className="w-3.5 h-3.5 text-rose-400" />
              VERIFICATION HALTED · ZERO REMOTE WRITES
            </span>
          ) : (
            <span className="px-3 py-1 rounded-lg bg-zinc-900 border border-zinc-700 text-zinc-300 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-indigo-400 animate-spin" />
              PIPELINE EXECUTING (ISOLATED WORKSPACE)
            </span>
          )}
        </div>
      </div>

      {/* Connected Continuous Rail Track */}
      <div className="relative">
        {/* Continuous Horizontal Structural Rail (Desktop) */}
        <div
          className="hidden lg:block absolute top-[27px] left-8 right-8 h-[2px] bg-zinc-800 pointer-events-none z-0"
          aria-hidden="true"
        >
          <div
            className={`h-full transition-all duration-500 ${
              isFailed
                ? "bg-rose-600/80 shadow-[0_0_8px_rgba(244,63,94,0.5)]"
                : isVerified
                ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"
                : "bg-indigo-500"
            }`}
            style={{
              width: isVerified
                ? "100%"
                : isFailed
                ? `${((failedIndex + 0.5) / 6) * 100}%`
                : `${((Math.max(activeIndex, 0) + 0.5) / 6) * 100}%`,
            }}
          />
        </div>

        {/* 6 Discrete Stage Machine Nodes */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 relative z-10">
          {STAGES.map((stage, idx) => {
            const Icon = stage.icon;
            let nodeStatus: "complete" | "active" | "failed" | "blocked" | "pending" = "pending";

            if (isFailed) {
              if (idx < failedIndex) {
                nodeStatus = "complete";
              } else if (idx === failedIndex) {
                nodeStatus = "failed";
              } else {
                nodeStatus = "blocked";
              }
            } else if (isVerified) {
              if (idx < 5) {
                nodeStatus = "complete";
              } else {
                nodeStatus =
                  job.pr_number ||
                  ["pr_created", "pr_updated", "pr_merged"].includes(state)
                    ? "complete"
                    : "active";
              }
            } else {
              if (idx < activeIndex) {
                nodeStatus = "complete";
              } else if (idx === activeIndex) {
                nodeStatus = "active";
              } else {
                nodeStatus = "pending";
              }
            }

            let badgeStyles = "bg-zinc-900 border-zinc-800 text-zinc-500";
            let cardStyles = "bg-zinc-950/40 border-border-subtle/70 text-zinc-400";
            let statusBadge = (
              <span className="text-[10px] font-mono text-zinc-500 uppercase font-semibold">Pending</span>
            );

            if (nodeStatus === "complete") {
              badgeStyles = "bg-emerald-950 border-emerald-600 text-emerald-300 ring-2 ring-emerald-900/40";
              cardStyles = "bg-emerald-950/15 border-emerald-800/50 text-zinc-200 shadow-sm";
              statusBadge = (
                <span className="text-[10px] font-mono text-emerald-400 font-bold uppercase flex items-center gap-1">
                  <Check className="w-3 h-3" /> Sealed
                </span>
              );
            } else if (nodeStatus === "active") {
              badgeStyles = "bg-indigo-950 border-indigo-500 text-indigo-200 ring-4 ring-indigo-500/20 shadow-[0_0_16px_rgba(99,102,241,0.4)]";
              cardStyles = "bg-zinc-900 border-indigo-500 text-zinc-100 shadow-lg ring-1 ring-indigo-500/40";
              statusBadge = (
                <span className="text-[10px] font-mono text-indigo-300 font-bold uppercase flex items-center gap-1">
                  <Clock className="w-3 h-3 animate-spin text-indigo-400" /> Running
                </span>
              );
            } else if (nodeStatus === "failed") {
              badgeStyles = "bg-rose-950 border-rose-600 text-rose-200 ring-4 ring-rose-600/30 shadow-[0_0_16px_rgba(244,63,94,0.4)]";
              cardStyles = "bg-rose-950/25 border-rose-700 text-rose-200 ring-1 ring-rose-700/50";
              statusBadge = (
                <span className="text-[10px] font-mono text-rose-400 font-bold uppercase flex items-center gap-1">
                  <X className="w-3 h-3" /> Halted
                </span>
              );
            } else if (nodeStatus === "blocked") {
              badgeStyles = "bg-zinc-950 border-zinc-900 text-zinc-700";
              cardStyles = "bg-zinc-950/60 border-zinc-900/80 opacity-40";
              statusBadge = (
                <span className="text-[10px] font-mono text-zinc-600 uppercase font-semibold">Blocked</span>
              );
            }

            return (
              <div
                key={stage.id}
                className={`p-4 rounded-xl border flex flex-col justify-between transition-all duration-200 relative ${cardStyles}`}
              >
                {/* Top Row: Stage Index & Illuminated Node Icon */}
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[11px] font-mono font-black tracking-wider text-zinc-400">
                    {stage.stepNum}
                  </span>
                  <div
                    className={`w-7 h-7 rounded-lg flex items-center justify-center border shrink-0 transition-all ${badgeStyles}`}
                  >
                    <Icon className="w-4 h-4" />
                  </div>
                </div>

                {/* Middle: Stage Identity */}
                <div className="space-y-1 my-1">
                  <div className="text-xs font-bold font-mono tracking-tight text-zinc-100">
                    {stage.label}
                  </div>
                  <div className="text-[11px] text-zinc-400 font-sans leading-tight">
                    {stage.shortDesc}
                  </div>
                </div>

                {/* Bottom: Live Telemetry State Indicator */}
                <div className="pt-2.5 mt-2.5 border-t border-zinc-800/60 flex items-center justify-between">
                  {statusBadge}
                  {idx < 5 && (
                    <ArrowRight className="w-3 h-3 text-zinc-600 hidden lg:block opacity-30" />
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Outcome Precision Summary Panels */}
      {isVerified && (
        <div className="p-4 rounded-xl bg-emerald-950/30 border border-emerald-800/70 text-emerald-200 font-mono text-xs space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-emerald-300 font-bold uppercase tracking-wider text-[11px]">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Attestation Sealed — Patch Verified Safe for Production</span>
            </div>
            <span className="text-[10px] text-emerald-400 font-mono">ED25519 SIGNED</span>
          </div>
          <p className="text-emerald-100/90 font-sans text-xs leading-relaxed">
            The synthesized AST remediation completed 0-egress sandbox verification and zero-regression security re-scans.
            Write authorization granted for Pull Request creation.
          </p>
        </div>
      )}

      {isFailed && (
        <div className="p-4 rounded-xl bg-rose-950/30 border border-rose-800 text-rose-200 font-mono text-xs space-y-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-rose-300 font-bold uppercase tracking-wider text-[11px]">
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>VERIFICATION HALTED AT GATE {STAGES[failedIndex]?.stepNum || "04"} / {STAGES[failedIndex]?.label || "VERIFY"}</span>
            </div>
            <span className="text-[10px] text-rose-400 font-mono font-bold bg-rose-950 px-2 py-0.5 rounded border border-rose-800">
              WRITE AUTHORIZATION: DENIED
            </span>
          </div>
          <p className="text-zinc-300 font-sans text-xs leading-relaxed">
            The automated remediation pipeline safely halted execution at the failing security gate. In accordance with PatchProof fail-closed policy invariants, downstream proof generation and GitHub write authorization were strictly prevented. Zero remote writes occurred.
          </p>
          <div className="p-3 rounded-lg bg-zinc-950 border border-rose-900/80 font-mono text-[11px] text-rose-300 break-all">
            <span className="text-[10px] uppercase text-zinc-500 font-bold block mb-1">
              Halt Diagnostic:
            </span>
            {job.error || "Automated test assertions or security policy constraints were violated."}
          </div>
        </div>
      )}
    </div>
  );
}
