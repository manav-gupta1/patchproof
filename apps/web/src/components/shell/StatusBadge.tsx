"use client";

import React from "react";
import { getStatusTheme, cn } from "@/lib/utils";

interface StatusBadgeProps {
  status?: string | null;
  size?: "sm" | "md";
  showDot?: boolean;
  className?: string;
}

export function StatusBadge({
  status,
  size = "md",
  showDot = true,
  className,
}: StatusBadgeProps) {
  const theme = getStatusTheme(status);

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 font-mono uppercase tracking-wider font-semibold border rounded-full",
        size === "sm" ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs",
        theme.badgeClass,
        className
      )}
      data-testid="status-badge"
    >
      {showDot && (
        <span
          className={cn(
            "rounded-full shrink-0",
            size === "sm" ? "w-1.5 h-1.5" : "w-2 h-2",
            theme.dotClass
          )}
          aria-hidden="true"
        />
      )}
      <span>{theme.label}</span>
    </span>
  );
}
