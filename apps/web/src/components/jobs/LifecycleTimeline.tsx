"use client";

import React from "react";
import { Check, X, Clock, AlertTriangle, Terminal, Shield } from "lucide-react";
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
  {
    key: "pr_created",
    label: "PR Created",
    matchStates: ["pr_created", "pr_updated", "pr_merged"],
  },
];

function formatEventTimestamp(isoStr?: string | null): string {
  if (!isoStr) return "--:--:--";
  try {
    const d = new Date(isoStr);
    return d.toTimeString().split(" ")[0];
  } catch {
    return "--:--:--";
  }
}

function getStageBadge(stateStr: string): { tag: string; color: string } {
  const s = stateStr.toLowerCase();
  if (s.includes("scan") || s.includes("queue")) return { tag: "SCANNER", color: "text-zinc-300 border-zinc-700 bg-zinc-900" };
  if (s.includes("analyz") || s.includes("ast")) return { tag: "AST", color: "text-indigo-300 border-indigo-800 bg-indigo-950/60" };
  if (s.includes("patch")) return { tag: "PATCH", color: "text-cyan-300 border-cyan-800 bg-cyan-950/60" };
  if (s.includes("verify") || s.includes("sandbox")) return { tag: "SANDBOX", color: "text-amber-300 border-amber-800 bg-amber-950/60" };
  if (s.includes("verified") || s.includes("proof")) return { tag: "PROOF", color: "text-emerald-300 border-emerald-800 bg-emerald-950/60" };
  if (s.includes("pr_") || s.includes("write")) return { tag: "GITHUB", color: "text-emerald-300 border-emerald-800 bg-emerald-950/60" };
  if (s.includes("fail")) return { tag: "SECURITY", color: "text-rose-300 border-rose-800 bg-rose-950/60" };
  return { tag: "ORCHESTRATOR", color: "text-zinc-300 border-zinc-700 bg-zinc-900" };
}

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
      const idx = ORDERED_STEPS.findIndex((s) =>
        s.matchStates.includes(prevToState)
      );
      if (idx !== -1) failedAtStepIndex = Math.min(idx + 1, ORDERED_STEPS.length - 1);
    }
  }

  return (
    <div
      className="border border-border-subtle bg-surface-200 rounded-xl p-5 sm:p-6 space-y-5"
      data-testid="lifecycle-timeline"
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-border-subtle">
        <div>
          <div className="text-[11px] font-mono uppercase tracking-wider text-zinc-400 font-medium flex items-center gap-1.5">
            <Terminal className="w-3.5 h-3.5 text-zinc-400" />
            <span>Audit Trail & Telemetry</span>
          </div>
          <h3 className="text-base font-bold text-zinc-100 font-sans mt-0.5 tracking-tight">
            Security Control Plane Event Stream
          </h3>
        </div>
        {job.is_stale && (
          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-amber-950/60 border border-amber-800 text-amber-300 text-xs font-mono rounded-lg">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Stale for Current Head SHA</span>
          </div>
        )}
      </div>

      {/* Step Transition Indicator (Keeps data-testid and test requirements) */}
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
              status =
                currentStepIndex === ORDERED_STEPS.length - 1
                  ? "completed"
                  : "current";
            } else {
              status = "pending";
            }
          } else if (currentState === "verified" && idx <= 5) {
            status = "completed";
          }

          const stepEvent = eventMap.get(step.key);
          const stepTime = stepEvent?.created_at
            ? formatDate(stepEvent.created_at)
            : null;

          return (
            <div
              key={step.key}
              className={cn(
                "p-2.5 rounded-lg border flex flex-col justify-between transition-colors",
                status === "completed" && "bg-zinc-900/60 border-zinc-800 text-zinc-300",
                status === "current" && "bg-zinc-800 border-zinc-600 text-zinc-100 font-medium ring-1 ring-zinc-500/20",
                status === "failed" && "bg-rose-950/40 border-rose-800 text-rose-300",
                status === "pending" && "bg-zinc-950/40 border-zinc-900/60 text-zinc-600"
              )}
              data-testid={`timeline-step-${step.key}`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] text-zinc-500 font-bold">0{idx + 1}</span>
                <div
                  className={cn(
                    "w-4 h-4 rounded flex items-center justify-center text-[10px]",
                    status === "completed" && "text-emerald-400",
                    status === "current" && "text-indigo-400",
                    status === "failed" && "text-rose-400",
                    status === "pending" && "text-zinc-600"
                  )}
                >
                  {status === "completed" && <Check className="w-3.5 h-3.5 stroke-[2.5]" />}
                  {status === "current" && <Clock className="w-3.5 h-3.5 animate-spin" />}
                  {status === "failed" && <X className="w-3.5 h-3.5 stroke-[2.5]" />}
                  {status === "pending" && <span className="w-1.5 h-1.5 rounded-full bg-zinc-700" />}
                </div>
              </div>

              <div>
                <div className="text-xs text-zinc-200 font-sans truncate font-medium">
                  {status === "failed" ? `${step.label} Failed` : step.label}
                </div>
                {stepTime ? (
                  <div className="text-[10px] text-zinc-400 mt-0.5 truncate">{stepTime}</div>
                ) : (
                  <div className="text-[10px] text-zinc-400 mt-0.5 font-mono">
                    {status === "current" ? "Active" : "—"}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Real-time Forensic Terminal Event Stream */}
      <div
        className="rounded-lg border border-border-subtle bg-zinc-950/90 overflow-hidden font-mono text-xs"
        aria-live="polite"
        aria-label="Security control plane event stream"
      >
        <div className="px-4 py-2 bg-surface-300/40 border-b border-border-subtle flex items-center justify-between">
          <div className="flex items-center gap-2 text-[11px] text-zinc-400 uppercase tracking-wider font-semibold">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Live Event Journal
          </div>
          <span className="text-[10px] text-zinc-500">{events.length} transition events recorded</span>
        </div>

        <div className="p-3 space-y-2 max-h-64 overflow-y-auto divide-y divide-zinc-900/60">
          {events.length === 0 ? (
            <div className="text-zinc-500 py-3 text-center text-xs">
              Awaiting first telemetry event from worker daemon...
            </div>
          ) : (
            events.map((ev, i) => {
              const stage = getStageBadge(ev.to_state || "");
              return (
                <div key={ev.id || i} className="pt-2 first:pt-0 flex items-start gap-3">
                  <span className="text-zinc-500 shrink-0 text-[11px] font-mono select-none">
                    {formatEventTimestamp(ev.created_at)}
                  </span>
                  <span
                    className={`px-1.5 py-0.2 rounded border text-[10px] uppercase font-bold shrink-0 ${stage.color}`}
                  >
                    {stage.tag}
                  </span>
                  <span className="text-zinc-300 text-xs flex-1 break-words font-sans">
                    {ev.message || `State transition to ${ev.to_state}`}
                  </span>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
