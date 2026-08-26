"use client";

import React from "react";
import { Inbox } from "lucide-react";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  title,
  description,
  icon,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-12 text-center rounded-md border border-dashed border-border-muted bg-zinc-900/20",
        className
      )}
      data-testid="empty-state"
    >
      <div className="w-10 h-10 rounded bg-zinc-900 flex items-center justify-center text-zinc-500 mb-3 border border-border-subtle">
        {icon || <Inbox className="w-5 h-5" />}
      </div>
      <h3 className="text-sm font-semibold text-zinc-200 mb-1 font-sans">{title}</h3>
      <p className="text-xs text-zinc-400 max-w-md mb-5 leading-relaxed font-sans">
        {description}
      </p>
      {action && <div>{action}</div>}
    </div>
  );
}
