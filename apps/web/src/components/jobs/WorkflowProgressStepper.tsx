"use client";

import React from "react";
import { Check, X, Clock, ShieldAlert } from "lucide-react";
import { JobStatusResponse } from "@/lib/types";

interface WorkflowProgressStepperProps {
  job: JobStatusResponse;
}

export function WorkflowProgressStepper({ job }: WorkflowProgressStepperProps) {
  const state = (job.state || "queued").toLowerCase();
  const isFailed = state === "failed";
  const isVerified = ["verified", "pr_created", "pr_updated", "pr_merged"].includes(state);
  const events = job.events || [];
  const errorMsg = (job.error || "").toLowerCase();

  // Canonical stage progression
  // 0: Finding Ingestion (queued, scanning)
  // 1: AST Patch Synthesis (analyzing, patching)
  // 2: Sandbox Verification (verifying)
  // 3: Zero-Regression Gates (re-scan & syntax verification)
  // 4: Cryptographic Proof (signing evidence)
  // 5: GitHub Delivery (pr_created, pr_updated, pr_merged)

  let activeIndex = -1;
  let failedIndex = -1;

  if (state === "queued" || state === "scanning") {
    activeIndex = 0;
  } else if (state === "analyzing" || state === "patching") {
    activeIndex = 1;
  } else if (state === "verifying") {
    activeIndex = 2;
  } else if (state === "verified") {
    activeIndex = 5;
  } else if (["pr_created", "pr_updated", "pr_merged"].includes(state)) {
    activeIndex = 6;
  } else if (isFailed) {
    // Determine the exact failing stage based on transition history & error context
    const reachedStates = new Set(events.map((e) => (e.to_state || "").toLowerCase()));
    
    if (errorMsg.includes("policy") || (job.policy && !job.policy.allowed)) {
      failedIndex = 3; // Policy gate blocked
    } else if (errorMsg.includes("sandbox") || errorMsg.includes("gvisor") || errorMsg.includes("test") || errorMsg.includes("regression") || reachedStates.has("verifying")) {
      failedIndex = 2; // Sandbox / regression test failed
    } else if (errorMsg.includes("patch") || errorMsg.includes("ast") || errorMsg.includes("syntax") || reachedStates.has("patching") || reachedStates.has("analyzing")) {
      failedIndex = 1; // AST / patch synthesis failed
    } else if (errorMsg.includes("github") || errorMsg.includes("token") || errorMsg.includes("pull request") || reachedStates.has("verified")) {
      failedIndex = 5; // GitHub delivery failed
    } else {
      failedIndex = 0; // Ingestion / staging / queue failure
    }
  }

  const stepDefs = [
    {
      id: "detection",
      label: "Finding Ingestion",
      detail: state === "queued" ? "Queued in runner" : "Alert & repository staged",
    },
    {
      id: "patch",
      label: "AST Patch Synthesis",
      detail: "Deterministic rule proposal",
    },
    {
      id: "sandbox",
      label: "Sandbox Verification",
      detail: "Isolated gVisor execution",
    },
    {
      id: "gates",
      label: "Zero-Regression Gates",
      detail: "Exploit elimination & re-scan",
    },
    {
      id: "evidence",
      label: "Cryptographic Proof",
      detail: "Ed25519 signature & digest",
    },
    {
      id: "delivery",
      label: "GitHub Delivery",
      detail: job.pr_number ? `PR #${job.pr_number} created` : "Zero writes if blocked",
    },
  ];

  return (
    <div className="border border-border-subtle bg-surface-300 rounded-lg p-4" data-testid="workflow-progress-stepper">
      <div className="flex items-center justify-between mb-3 text-xs">
        <span className="text-[11px] font-mono uppercase tracking-wider text-zinc-500">
          Remediation Pipeline
        </span>
        <span className="text-[11px] font-mono text-zinc-400">
          {isVerified
            ? "6 of 6 verified"
            : isFailed
            ? `Halted at step ${failedIndex + 1} of 6 (Zero writes)`
            : `Step ${Math.min(activeIndex + 1, 6)} of 6`}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
        {stepDefs.map((step, idx) => {
          let status: "complete" | "active" | "failed" | "blocked" | "pending" = "pending";

          if (isFailed) {
            if (idx < failedIndex) {
              status = "complete";
            } else if (idx === failedIndex) {
              status = "failed";
            } else {
              status = "blocked";
            }
          } else if (isVerified) {
            if (idx < 5) {
              status = "complete";
            } else {
              status = job.pr_number || ["pr_created", "pr_updated", "pr_merged"].includes(state) ? "complete" : "active";
            }
          } else {
            if (idx < activeIndex) {
              status = "complete";
            } else if (idx === activeIndex) {
              status = "active";
            } else {
              status = "pending";
            }
          }

          let badgeColor = "bg-zinc-900 border-zinc-800 text-zinc-500";
          let icon = <span className="text-[10px] font-mono">0{idx + 1}</span>;

          if (status === "failed") {
            badgeColor = "bg-rose-950/80 border-rose-800 text-rose-400";
            icon = <X className="w-3 h-3 text-rose-400" />;
          } else if (status === "complete") {
            badgeColor = "bg-emerald-950/80 border-emerald-800 text-emerald-400";
            icon = <Check className="w-3 h-3 text-emerald-400" />;
          } else if (status === "active") {
            badgeColor = "bg-zinc-800 border-zinc-600 text-zinc-200";
            icon = <Clock className="w-3 h-3 text-indigo-400 animate-spin" />;
          } else if (status === "blocked") {
            badgeColor = "bg-zinc-950 border-zinc-900 text-zinc-600";
            icon = <span className="text-[9px] font-mono text-zinc-600">--</span>;
          }

          return (
            <div
              key={step.id}
              className={`p-2.5 rounded border flex flex-col justify-between transition-colors ${
                status === "active"
                  ? "bg-zinc-900 border-zinc-700 shadow-sm"
                  : status === "failed"
                  ? "bg-rose-950/20 border-rose-900/60"
                  : status === "blocked"
                  ? "bg-zinc-950/60 border-zinc-900/60 opacity-60"
                  : "bg-zinc-900/40 border-zinc-800/80"
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] font-mono text-zinc-500">0{idx + 1}</span>
                <div className={`w-5 h-5 rounded flex items-center justify-center border shrink-0 ${badgeColor}`}>
                  {icon}
                </div>
              </div>

              <div>
                <div className="text-xs font-semibold text-zinc-200 font-sans leading-tight truncate">
                  {step.label}
                </div>
                <div className="text-[10px] text-zinc-500 font-mono mt-0.5 truncate">
                  {status === "blocked" ? "Blocked / Not Run" : step.detail}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
