"use client";

import React from "react";
import { Shield, KeyRound, Server, Menu } from "lucide-react";

interface TopNavProps {
  tenantName?: string;
  apiStatus?: string;
  onOpenMobileMenu?: () => void;
}

export function TopNav({
  tenantName = "Default Tenant",
  apiStatus = "healthy",
  onOpenMobileMenu,
}: TopNavProps) {
  const isHealthy = apiStatus === "healthy";

  return (
    <header className="h-14 border-b border-border-subtle bg-surface-400 px-4 sm:px-6 flex items-center justify-between z-10 select-none">
      {/* Left: Mobile Toggle & Tenant Info */}
      <div className="flex items-center gap-3">
        {onOpenMobileMenu && (
          <button
            onClick={onOpenMobileMenu}
            className="p-1.5 rounded text-zinc-400 hover:text-white hover:bg-zinc-800 md:hidden focus:outline-none focus-visible:ring-1 focus-visible:ring-zinc-400"
            aria-label="Open navigation menu"
            data-testid="mobile-menu-button"
          >
            <Menu className="w-4 h-4" />
          </button>
        )}

        <div className="flex items-center gap-2 text-xs font-mono text-zinc-300">
          <span className="text-zinc-500">Tenant:</span>
          <span className="text-zinc-200 font-medium truncate max-w-[140px] sm:max-w-xs">
            {tenantName}
          </span>
        </div>
      </div>

      {/* Right: Auth Mode & API Health */}
      <div className="flex items-center gap-3">
        <div className="hidden sm:flex items-center gap-1.5 text-xs font-mono text-zinc-400">
          <span className="text-zinc-500">Auth:</span>
          <span className="text-zinc-300">Bearer Scoped</span>
        </div>

        <div className="h-3 w-px bg-zinc-800 hidden sm:block" />

        <div className="flex items-center gap-1.5 text-xs font-mono">
          <span className="text-zinc-500 hidden sm:inline">API:</span>
          <span
            className={`inline-flex items-center gap-1 font-medium ${
              isHealthy ? "text-emerald-400" : "text-amber-400"
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                isHealthy ? "bg-emerald-400" : "bg-amber-400"
              }`}
            />
            {apiStatus.toUpperCase()}
          </span>
        </div>
      </div>
    </header>
  );
}
