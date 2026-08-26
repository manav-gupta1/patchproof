"use client";

import React from "react";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface LoadingSpinnerProps {
  label?: string;
  message?: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function LoadingSpinner({
  label,
  message,
  size = "md",
  className,
}: LoadingSpinnerProps) {
  const displayLabel = message || label || "Loading...";
  const sizeClass =
    size === "sm" ? "w-4 h-4" : size === "lg" ? "w-8 h-8" : "w-5 h-5";

  return (
    <div
      className={cn("flex flex-col items-center justify-center p-8 gap-3", className)}
      data-testid="loading-spinner"
    >
      <Loader2 className={cn("animate-spin text-zinc-400", sizeClass)} />
      {displayLabel && <p className="text-xs font-mono text-zinc-400">{displayLabel}</p>}
    </div>
  );
}
