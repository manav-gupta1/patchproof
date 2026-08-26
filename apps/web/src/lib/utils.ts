import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatSha(sha?: string | null, length: number = 7): string {
  if (!sha) return "—";
  return sha.slice(0, length);
}

export function formatDate(dateString?: string | null): string {
  if (!dateString) return "—";
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return String(dateString);
    return d.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  } catch {
    return String(dateString);
  }
}

export function formatRelativeTime(dateString?: string | null): string {
  if (!dateString) return "—";
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return String(dateString);
    const now = new Date();
    const diffSec = Math.floor((now.getTime() - d.getTime()) / 1000);

    if (diffSec < 10) return "just now";
    if (diffSec < 60) return `${diffSec}s ago`;
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h ago`;
    const diffDay = Math.floor(diffHr / 24);
    return `${diffDay}d ago`;
  } catch {
    return String(dateString);
  }
}

export function getStatusTheme(state?: string | null): {
  label: string;
  badgeClass: string;
  dotClass: string;
  borderClass: string;
} {
  const s = (state || "unknown").toLowerCase();

  switch (s) {
    case "pr_created":
    case "pr_merged":
    case "verified":
      return {
        label: s === "pr_created" ? "PR CREATED" : s === "pr_merged" ? "MERGED" : "VERIFIED",
        badgeClass: "bg-emerald-950/80 text-emerald-300 border-emerald-800/60",
        dotClass: "bg-emerald-400 animate-pulse",
        borderClass: "border-emerald-500/30",
      };
    case "pr_updated":
      return {
        label: "PR UPDATED",
        badgeClass: "bg-cyan-950/80 text-cyan-300 border-cyan-800/60",
        dotClass: "bg-cyan-400",
        borderClass: "border-cyan-500/30",
      };
    case "queued":
      return {
        label: "QUEUED",
        badgeClass: "bg-slate-900/80 text-slate-300 border-slate-700/60",
        dotClass: "bg-slate-400",
        borderClass: "border-slate-700/30",
      };
    case "scanning":
      return {
        label: "SCANNING",
        badgeClass: "bg-indigo-950/80 text-indigo-300 border-indigo-800/60",
        dotClass: "bg-indigo-400 animate-pulse",
        borderClass: "border-indigo-500/30",
      };
    case "analyzing":
      return {
        label: "ANALYZING",
        badgeClass: "bg-blue-950/80 text-blue-300 border-blue-800/60",
        dotClass: "bg-blue-400 animate-pulse",
        borderClass: "border-blue-500/30",
      };
    case "patching":
      return {
        label: "PATCHING",
        badgeClass: "bg-purple-950/80 text-purple-300 border-purple-800/60",
        dotClass: "bg-purple-400 animate-pulse",
        borderClass: "border-purple-500/30",
      };
    case "verifying":
      return {
        label: "VERIFYING",
        badgeClass: "bg-amber-950/80 text-amber-300 border-amber-800/60",
        dotClass: "bg-amber-400 animate-pulse",
        borderClass: "border-amber-500/30",
      };
    case "failed":
      return {
        label: "FAILED",
        badgeClass: "bg-rose-950/80 text-rose-300 border-rose-800/60",
        dotClass: "bg-rose-500",
        borderClass: "border-rose-500/30",
      };
    case "stale":
    case "superseded":
      return {
        label: s === "superseded" ? "SUPERSEDED" : "STALE",
        badgeClass: "bg-amber-950/60 text-amber-400 border-amber-800/40",
        dotClass: "bg-amber-500",
        borderClass: "border-amber-600/30",
      };
    case "rolled_back":
      return {
        label: "ROLLED BACK",
        badgeClass: "bg-orange-950/80 text-orange-300 border-orange-800/60",
        dotClass: "bg-orange-500",
        borderClass: "border-orange-500/30",
      };
    case "pr_closed":
    case "closed":
      return {
        label: "CLOSED",
        badgeClass: "bg-slate-900/80 text-slate-400 border-slate-800/60",
        dotClass: "bg-slate-500",
        borderClass: "border-slate-800/30",
      };
    default:
      return {
        label: (state || "UNKNOWN").toUpperCase(),
        badgeClass: "bg-slate-900 text-slate-400 border-slate-800",
        dotClass: "bg-slate-500",
        borderClass: "border-slate-800",
      };
  }
}

export function getSeverityTheme(severity?: string | null): {
  label: string;
  badgeClass: string;
} {
  const s = (severity || "high").toUpperCase();
  switch (s) {
    case "CRITICAL":
      return {
        label: "CRITICAL",
        badgeClass: "bg-red-950/80 text-red-300 border border-red-800/60",
      };
    case "HIGH":
      return {
        label: "HIGH",
        badgeClass: "bg-orange-950/80 text-orange-300 border border-orange-800/60",
      };
    case "MEDIUM":
      return {
        label: "MEDIUM",
        badgeClass: "bg-amber-950/80 text-amber-300 border border-amber-800/60",
      };
    case "LOW":
      return {
        label: "LOW",
        badgeClass: "bg-blue-950/80 text-blue-300 border border-blue-800/60",
      };
    default:
      return {
        label: s,
        badgeClass: "bg-slate-800 text-slate-300 border border-slate-700",
      };
  }
}
