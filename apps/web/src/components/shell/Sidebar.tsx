"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Shield,
  GitFork,
  Cpu,
  GitPullRequest,
  ShieldCheck,
  Lock,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavGroup {
  label?: string;
  items: {
    name: string;
    href: string;
    icon: React.ElementType;
    badge?: string;
  }[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    items: [
      { name: "Overview", href: "/", icon: LayoutDashboard },
    ],
  },
  {
    label: "PROTECT",
    items: [
      { name: "Remediations", href: "/jobs", icon: Cpu },
      { name: "Repositories", href: "/repositories", icon: GitFork },
    ],
  },
  {
    label: "DELIVER",
    items: [
      { name: "Pull requests", href: "/pull-requests", icon: GitPullRequest },
    ],
  },
  {
    label: "SYSTEM",
    items: [
      { name: "Security & Posture", href: "/settings", icon: ShieldCheck },
    ],
  },
];

interface SidebarProps {
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export function Sidebar({ mobileOpen = false, onCloseMobile }: SidebarProps) {
  const pathname = usePathname();

  useEffect(() => {
    if (onCloseMobile) onCloseMobile();
  }, [pathname]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && mobileOpen && onCloseMobile) {
        onCloseMobile();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [mobileOpen, onCloseMobile]);

  return (
    <>
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm md:hidden"
          onClick={onCloseMobile}
          aria-hidden="true"
        />
      )}

      <aside
        className={cn(
          "w-60 bg-surface-300 border-r border-border-subtle flex flex-col shrink-0 min-h-screen select-none z-50 transition-transform duration-150 ease-out",
          "fixed inset-y-0 left-0 md:static md:translate-x-0",
          mobileOpen ? "translate-x-0 shadow-2xl" : "-translate-x-full md:translate-x-0"
        )}
        aria-label="Sidebar Navigation"
        data-testid="app-sidebar"
      >
        {/* Brand Header */}
        <div className="h-14 flex items-center justify-between px-5 border-b border-border-subtle">
          <Link
            href="/"
            className="flex items-center gap-2.5 group focus:outline-none focus-visible:ring-1 focus-visible:ring-zinc-400 rounded"
          >
            <div className="w-6 h-6 rounded bg-zinc-900 border border-zinc-700/80 flex items-center justify-center text-zinc-300">
              <Shield className="w-3.5 h-3.5" />
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-sm font-semibold tracking-tight text-zinc-100 font-sans">
                PatchProof
              </span>
              <span className="text-[10px] font-mono px-1 py-0.2 bg-zinc-800 text-zinc-400 border border-zinc-700/60 rounded">
                v0.1
              </span>
            </div>
          </Link>

          {onCloseMobile && (
            <button
              onClick={onCloseMobile}
              className="p-1 rounded text-zinc-400 hover:text-white hover:bg-zinc-800 md:hidden focus:outline-none focus-visible:ring-1 focus-visible:ring-zinc-400"
              aria-label="Close sidebar"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Navigation Groups */}
        <nav className="flex-1 py-3 px-2.5 space-y-4 overflow-y-auto">
          {NAV_GROUPS.map((group, groupIdx) => (
            <div key={groupIdx} className="space-y-0.5">
              {group.label && (
                <div className="px-2.5 pb-1 pt-1.5 text-[10px] font-mono font-medium uppercase tracking-wider text-zinc-500">
                  {group.label}
                </div>
              )}
              {group.items.map((item) => {
                const isActive =
                  item.href === "/"
                    ? pathname === "/"
                    : pathname.startsWith(item.href);
                const Icon = item.icon;

                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={cn(
                      "flex items-center justify-between px-2.5 py-1.5 rounded text-xs font-medium transition-colors duration-100 focus:outline-none focus-visible:ring-1 focus-visible:ring-zinc-400",
                      isActive
                        ? "bg-zinc-800/80 text-zinc-100 font-semibold"
                        : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900"
                    )}
                    aria-current={isActive ? "page" : undefined}
                  >
                    <div className="flex items-center gap-2">
                      <Icon
                        className={cn(
                          "w-3.5 h-3.5 shrink-0",
                          isActive ? "text-zinc-200" : "text-zinc-500"
                        )}
                      />
                      <span>{item.name}</span>
                    </div>
                    {item.badge && (
                      <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-zinc-800 text-zinc-400 border border-zinc-700">
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>

        {/* Protection Invariant Micro-Card */}
        <div className="p-2.5 mx-2.5 mb-2.5 bg-zinc-900/80 border border-border-subtle rounded text-[11px] text-zinc-400 space-y-1">
          <div className="flex items-center justify-between font-mono text-[10px] font-medium text-zinc-300">
            <span className="flex items-center gap-1.5">
              <Lock className="w-3 h-3 text-emerald-400" />
              Fail-closed invariant
            </span>
            <span className="text-emerald-400 text-[10px]">ACTIVE</span>
          </div>
          <p className="text-[10px] text-zinc-500 leading-tight">
            Unverified patch → 0 remote writes.
          </p>
        </div>

        {/* Footer / Status */}
        <div className="p-3 border-t border-border-subtle bg-surface-400 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span className="text-[11px] text-zinc-400 font-sans">Protection active</span>
          </div>
          <span className="text-[10px] font-mono text-zinc-500">0 egress</span>
        </div>
      </aside>
    </>
  );
}
