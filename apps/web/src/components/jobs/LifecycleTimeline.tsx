"use client";

import React from "react";
import { Check, X, Clock, AlertTriangle } from "lucide-react";
import { JobEvent, JobStatusResponse } from "@/lib/types";
import { formatDate, cn } from "@/lib/utils";

interface LifecycleTimelineProps {
  job: JobStatusResponse;
}

interface StepDef {
  key: string;
  label: string;
  matchStates: string[];
}

const ORDERED_STEPS: StepDef[] = [
  { key: "queued", label: "Queued", matchStates: ["queued"] },
  { key: "scanning", label: "Scanning", matchStates: ["scanning"] },
  { key: "analyzing", label: "Analyzing", matchStates: ["analyzing"] },
  { key: "patching", label: "Patching", matchStates: ["patching"] },
  { key: "verifying", label: "Verifying", matchStates: ["verifying"] },
  { key: "verified", label: "Verified", matchStates: ["verified"] },
  { key: "pr_created", label: "PR Created", matchStates: ["pr_created", "pr_updated", "pr_merged"] },
];

export function LifecycleTimeline({ job }: LifecycleTimelineProps) {
  const currentState = (job.state || "queued").toLowerCase();
  const isFailed = currentState === "failed";
  const events = job.events || [];

  const eventMap = new Map<string, JobEvent>();
  for (const ev of events) {
    if (ev.to_state) {
      eventMap.set(ev.to_state.toLowerCase(), ev);
    }
  }

  const currentStepIndex = ORDERED_STEPS.findIndex((step) =>
    step.matchStates.includes(currentState)
  );

  let failedAtStepIndex = 4;
  if (isFailed && events.length > 0) {
    const lastEvent = events[events.length - 1];
    const prevToState = lastEvent.from_state?.toLowerCase();
    if (prevToState) {
      const idx = ORDERED_STEPS.findIndex((s) => s.matchStates.includes(prevToState));
      if (idx !== -1) failedAtStepIndex = Math.min(idx + 1, ORDERED_STEPS.length - 1);
    }
  }

  return (
    <div className="border border-border-subtle bg-surface-300 rounded-lg p-5 space-y-4" data-testid="lifecycle-timeline">
      <div className="flex items-center justify-between pb-3 border-b border-border-subtle">
        <div>
          <div className="text-[11px] font-mono uppercase tracking-wider text-zinc-500">
            Event Log
          </div>
          <h3 className="text-sm font-semibold text-zinc-100 font-sans mt-0.5">
            Transition History
          </h3>
        </div>
        {job.is_stale && (
          <div className="flex items-center gap-1.5 px-2 py-0.5 bg-amber-950/60 border border-amber-800 text-amber-300 text-[11px] font-mono rounded">
            <AlertTriangle className="w-3 h-3" />
            <span>Stale for Head SHA</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-2 font-mono text-xs">
        {ORDERED_STEPS.map((step, idx) => {
          let status: "completed" | "current" | "pending" | "failed" = "pending";

          if (isFailed) {
            if (idx < failedAtStepIndex) {
              status = "completed";
            } else if (idx === failedAtStepIndex) {
              status = "failed";
            } else {
              status = "pending";
            }
          } else if (currentStepIndex !== -1) {
            if (idx < currentStepIndex) {
              status = "completed";
            } else if (idx === currentStepIndex) {
              status = currentStepIndex === ORDERED_STEPS.length - 1 ? "completed" : "current";
            } else {
              status = "pending";
            }
          } else if (currentState === "verified" && idx <= 5) {
            status = "completed";
          }

          const stepEvent = eventMap.get(step.key);
          const stepTime = stepEvent?.created_at ? formatDate(stepEvent.created_at) : null;

          return (
            <div
              key={step.key}
              className={cn(
                "p-2 rounded border flex flex-col justify-between transition-colors",
                status === "completed" && "bg-zinc-900/60 border-zinc-800 text-zinc-300",
                status === "current" && "bg-zinc-800 border-zinc-600 text-zinc-100 font-medium",
                status === "failed" && "bg-rose-950/40 border-rose-800 text-rose-300",
                status === "pending" && "bg-zinc-900/30 border-zinc-800/60 text-zinc-500"
              )}
              data-testid={`timeline-step-${step.key}`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] text-zinc-500">0{idx + 1}</span>
                <div
                  className={cn(
                    "w-4 h-4 rounded flex items-center justify-center text-[10px]",
                    status === "completed" && "text-emerald-400",
                    status === "current" && "text-indigo-400",
                    status === "failed" && "text-rose-400",
                    status === "pending" && "text-zinc-600"
                  )}
                >
                  {status === "completed" && <Check className="w-3 h-3 stroke-[2.5]" />}
                  {status === "current" && <Clock className="w-3 h-3 animate-pulse" />}
                  {status === "failed" && <X className="w-3 h-3 stroke-[2.5]" />}
                  {status === "pending" && <span className="w-1 h-1 rounded-full bg-zinc-600" />}
                </div>
              </div>

              <div>
                <div className="text-xs text-zinc-200 font-sans truncate">
                  {status === "failed" ? `${step.label} Failed` : step.label}
                </div>
                {stepTime ? (
                  <div className="text-[10px] text-zinc-500 mt-0.5 truncate">{stepTime}</div>
                ) : (
                  <div className="text-[10px] text-zinc-600 mt-0.5">
                    {status === "current" ? "Active" : "—"}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
