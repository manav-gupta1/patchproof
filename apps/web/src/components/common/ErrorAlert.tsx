"use client";

import React from "react";
import { AlertCircle, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

interface ErrorAlertProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorAlert({
  title = "Failed to load data",
  message,
  onRetry,
  className,
}: ErrorAlertProps) {
  return (
    <div
      className={cn(
        "rounded-md border border-rose-900/80 bg-rose-950/30 p-4 text-rose-200 flex items-start gap-3 font-mono text-xs",
        className
      )}
      data-testid="error-alert"
      role="alert"
    >
      <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
      <div className="flex-1">
        <h4 className="text-xs font-semibold text-rose-200 font-sans">{title}</h4>
        <p className="text-[11px] text-rose-300/80 mt-1 leading-relaxed">{message}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-2.5 inline-flex items-center gap-1.5 px-2.5 py-1 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-200 text-xs font-mono rounded transition-colors"
          >
            <RefreshCw className="w-3 h-3" />
            Retry
          </button>
        )}
      </div>
    </div>
  );
}
