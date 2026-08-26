"use client";

import React, { useState } from "react";
import { usePathname } from "next/navigation";
import { Sidebar } from "./Sidebar";
import { TopNav } from "./TopNav";
import { Header } from "../marketing/Header";
import { Footer } from "../marketing/Footer";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = usePathname() || "/";

  // Check if current route is part of the operational security console
  const isConsoleRoute =
    pathname.startsWith("/jobs") ||
    pathname.startsWith("/repositories") ||
    pathname.startsWith("/pull-requests") ||
    pathname.startsWith("/settings") ||
    pathname.startsWith("/dashboard");

  if (isConsoleRoute) {
    return (
      <div className="min-h-screen flex w-full bg-background text-foreground antialiased overflow-x-hidden">
        <Sidebar mobileOpen={mobileOpen} onCloseMobile={() => setMobileOpen(false)} />
        <div className="flex-1 flex flex-col min-w-0">
          <TopNav onOpenMobileMenu={() => setMobileOpen(true)} />
          <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto">{children}</main>
        </div>
      </div>
    );
  }

  // Public Marketing & Documentation Shell
  return (
    <div className="min-h-screen flex flex-col w-full bg-background text-foreground antialiased selection:bg-zinc-800 selection:text-zinc-100">
      <Header />
      <main className="flex-1">{children}</main>
      <Footer />
    </div>
  );
}
