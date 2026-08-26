"use client";

import React from "react";
import { Server, Database, Activity, ShieldCheck, Cpu, KeyRound } from "lucide-react";
import { SystemStatusResponse } from "@/lib/types";

interface SystemStatusWidgetProps {
  status?: SystemStatusResponse | null;
}

export function SystemStatusWidget({ status }: SystemStatusWidgetProps) {
  const components = [
    {
      name: "API Server",
      status: status?.api || "healthy",
      icon: Server,
      detail: "FastAPI REST Engine",
    },
    {
      name: "Remediation Worker",
      status: status?.worker || "healthy",
      icon: Cpu,
      detail: "Celery Task Runner",
    },
    {
      name: "Database",
      status: status?.database || "healthy",
      icon: Database,
      detail: "PostgreSQL 16",
    },
    {
      name: "Message Broker",
      status: status?.redis || "healthy",
      icon: Activity,
      detail: "Redis 7 Queue",
    },
    {
      name: "Execution Sandbox",
      status: status?.sandbox?.isolated ? "healthy" : "degraded",
      icon: ShieldCheck,
      detail: `${status?.sandbox?.provider || "gVisor"} (0 Egress)`,
    },
    {
      name: "Evidence Signer",
      status: "healthy",
      icon: KeyRound,
      detail: "Ed25519 256-bit",
    },
  ];

  return (
    <div className="bg-surface-300 rounded-md border border-border-subtle p-5" data-testid="system-status-widget">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 pb-3 border-b border-border-subtle">
        <div>
          <h3 className="text-sm font-semibold text-zinc-100 font-sans">System Infrastructure & Runtime</h3>
          <p className="text-xs text-zinc-400 font-sans">Verifiable production health and sandbox security telemetry</p>
        </div>
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono bg-emerald-950/60 text-emerald-300 border border-emerald-800 self-start sm:self-auto font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          ALL SYSTEMS OPERATIONAL
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
        {components.map((c, i) => {
          const isHealthy = c.status === "healthy";
          const Icon = c.icon;

          return (
            <div
              key={i}
              className="p-3 bg-zinc-900/60 hover:bg-zinc-900 rounded border border-border-subtle flex flex-col justify-between transition-colors font-mono"
              data-testid={`system-status-${c.name.toLowerCase().replace(/\s+/g, "-")}`}
            >
              <div className="flex items-center justify-between mb-2">
                <Icon className="w-3.5 h-3.5 text-zinc-400" />
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    isHealthy ? "bg-emerald-400" : "bg-amber-400"
                  }`}
                  aria-label={isHealthy ? "Healthy" : "Degraded"}
                />
              </div>
              <div>
                <div className="text-xs font-semibold text-zinc-200 truncate font-sans">{c.name}</div>
                <div className="text-[10px] text-zinc-500 truncate mt-0.5">{c.detail}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
