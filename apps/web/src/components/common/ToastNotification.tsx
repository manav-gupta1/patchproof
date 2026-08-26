"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, AlertTriangle, XCircle, X, ExternalLink } from "lucide-react";

export interface ToastItem {
  id: string;
  type: "success" | "warning" | "error" | "info";
  title: string;
  description: string;
  jobId?: string;
  durationMs?: number;
}

interface ToastContainerProps {
  toasts: ToastItem[];
  onDismiss: (id: string) => void;
}

export function ToastContainer({ toasts, onDismiss }: ToastContainerProps) {
  const router = useRouter();

  if (toasts.length === 0) return null;

  return (
    <div
      className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none"
      role="region"
      aria-label="Notifications"
      data-testid="toast-container"
    >
      {toasts.map((toast) => {
        const isSuccess = toast.type === "success";
        const isError = toast.type === "error";
        const isWarning = toast.type === "warning";

        return (
          <div
            key={toast.id}
            role="status"
            aria-live="polite"
            data-testid={`toast-${toast.id}`}
            onClick={() => {
              if (toast.jobId) {
                router.push(`/jobs/${encodeURIComponent(toast.jobId)}`);
                onDismiss(toast.id);
              }
            }}
            className={`pointer-events-auto p-3.5 rounded-md border shadow-2xl transition-all animate-in slide-in-from-bottom-2 duration-200 cursor-pointer ${
              isSuccess
                ? "bg-zinc-950 border-emerald-800/80 text-emerald-100 hover:border-emerald-600"
                : isError
                ? "bg-zinc-950 border-rose-800/80 text-rose-100 hover:border-rose-600"
                : isWarning
                ? "bg-zinc-950 border-amber-800/80 text-amber-100 hover:border-amber-600"
                : "bg-zinc-950 border-zinc-700 text-zinc-100 hover:border-zinc-500"
            }`}
          >
            <div className="flex items-start gap-2.5">
              <div className="shrink-0 mt-0.5">
                {isSuccess && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                {isError && <XCircle className="w-4 h-4 text-rose-400" />}
                {isWarning && <AlertTriangle className="w-4 h-4 text-amber-400" />}
                {!isSuccess && !isError && !isWarning && <CheckCircle2 className="w-4 h-4 text-zinc-400" />}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold font-mono tracking-tight">{toast.title}</p>
                <p className="text-[11px] text-zinc-400 font-mono truncate mt-0.5">{toast.description}</p>
                {toast.jobId && (
                  <span className="inline-flex items-center gap-1 text-[10px] text-zinc-400 hover:text-white mt-1 font-mono">
                    View job <ExternalLink className="w-2.5 h-2.5" />
                  </span>
                )}
              </div>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onDismiss(toast.id);
                }}
                className="shrink-0 p-1 text-zinc-400 hover:text-white rounded transition-colors focus:outline-none focus:ring-1 focus:ring-zinc-400"
                aria-label="Dismiss notification"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}
