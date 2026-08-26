"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  label: string;
  value: string | number;
  sublabel?: string;
  icon?: React.ReactNode;
  variant?: "default" | "emerald" | "indigo" | "rose" | "amber";
  className?: string;
  testId?: string;
}

export function MetricCard({
  label,
  value,
  sublabel,
  icon,
  variant = "default",
  className,
  testId,
}: MetricCardProps) {
  return (
    <div
      className={cn(
        "p-4 sm:p-5 flex flex-col justify-between transition-colors bg-surface-300",
        className
      )}
      data-testid={testId || `metric-card-${label.toLowerCase().replace(/\s+/g, "-")}`}
    >
      <div className="flex items-center justify-between gap-2 mb-1.5">
        <span className="text-[11px] font-mono uppercase tracking-wider text-zinc-400">
          {label}
        </span>
        {icon && <div className="text-zinc-400">{icon}</div>}
      </div>
      <div>
        <div className="text-2xl font-bold font-mono tracking-tight text-zinc-100">
          {value}
        </div>
        {sublabel && (
          <p className="text-[11px] text-zinc-400 mt-0.5 font-mono">{sublabel}</p>
        )}
      </div>
    </div>
  );
}
