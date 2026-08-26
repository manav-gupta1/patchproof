"use client";

import React from "react";
import { Check, X, Clock } from "lucide-react";
import { JobStatusResponse } from "@/lib/types";

interface WorkflowProgressStepperProps {
  job: JobStatusResponse;
}

export function WorkflowProgressStepper({ job }: WorkflowProgressStepperProps) {
  const state = (job.state || "queued").toLowerCase();
  const isFailed = state === "failed";
  const isVerified = ["verified", "pr_created", "pr_updated", "pr_merged"].includes(state);

  const steps = [
    {
      id: "detection",
      label: "Finding Ingestion",
      detail: "Alert authorized",
      isComplete: true,
      isActive: ["queued", "scanning"].includes(state),
      isFailed: false,
    },
    {
      id: "patch",
      label: "AST Patch Synthesis",
      detail: "Rule proposal",
      isComplete: ["analyzing", "patching", "verifying", "verified", "pr_created", "pr_updated", "pr_merged"].includes(state) || isFailed,
      isActive: state === "patching" || state === "analyzing",
      isFailed: false,
    },
    {
      id: "sandbox",
      label: "Sandbox Verification",
      detail: "gVisor isolation",
      isComplete: ["verified", "pr_created", "pr_updated", "pr_merged"].includes(state),
      isActive: state === "verifying",
      isFailed: isFailed,
    },
    {
      id: "gates",
      label: "Zero-Regression Gates",
      detail: "Re-scan passed",
      isComplete: ["verified", "pr_created", "pr_updated", "pr_merged"].includes(state),
      isActive: false,
      isFailed: isFailed,
    },
    {
      id: "evidence",
      label: "Cryptographic Proof",
      detail: "Ed25519 signature",
      isComplete: ["verified", "pr_created", "pr_updated", "pr_merged"].includes(state),
      isActive: false,
      isFailed: isFailed,
    },
    {
      id: "delivery",
      label: "GitHub Delivery",
      detail: job.pr_number ? `PR #${job.pr_number} created` : "PR publication",
      isComplete: ["pr_created", "pr_updated", "pr_merged"].includes(state),
      isActive: state === "verified",
      isFailed: isFailed,
    },
  ];

  return (
    <div className="border border-border-subtle bg-surface-300 rounded-lg p-4" data-testid="workflow-progress-stepper">
      <div className="flex items-center justify-between mb-3 text-xs">
        <span className="text-[11px] font-mono uppercase tracking-wider text-zinc-500">
          Remediation Pipeline
        </span>
        <span className="text-[11px] font-mono text-zinc-400">
          {isVerified ? "6 of 6 verified" : isFailed ? "Halted at verification gate" : "Executing"}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
        {steps.map((step, idx) => {
          let badgeColor = "bg-zinc-900 border-zinc-800 text-zinc-500";
          let icon = <span className="text-[10px] font-mono">0{idx + 1}</span>;

          if (step.isFailed) {
            badgeColor = "bg-rose-950/80 border-rose-800 text-rose-400";
            icon = <X className="w-3 h-3 text-rose-400" />;
          } else if (step.isComplete) {
            badgeColor = "bg-emerald-950/80 border-emerald-800 text-emerald-400";
            icon = <Check className="w-3 h-3 text-emerald-400" />;
          } else if (step.isActive) {
            badgeColor = "bg-zinc-800 border-zinc-600 text-zinc-200";
            icon = <Clock className="w-3 h-3 text-indigo-400 animate-spin" />;
          }

          return (
            <div
              key={step.id}
              className={`p-2.5 rounded border flex flex-col justify-between transition-colors ${
                step.isActive
                  ? "bg-zinc-900 border-zinc-700"
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
                  {step.detail}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
