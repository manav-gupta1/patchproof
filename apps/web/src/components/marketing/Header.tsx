"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Shield, Menu, X, ArrowRight, Github } from "lucide-react";

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const pathname = usePathname();

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [pathname]);

  // Lock body scroll when mobile menu is open
  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [mobileMenuOpen]);

  const navLinks = [
    { href: "/how-it-works", label: "How It Works" },
    { href: "/security", label: "Security & Trust" },
    { href: "/docs", label: "Docs" },
    { href: "/pricing", label: "Pricing" },
    { href: "/faq", label: "FAQ" },
    { href: "/contact", label: "Contact" },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border-subtle bg-surface-400/90 backdrop-blur-md">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        {/* Brand */}
        <Link
          href="/"
          className="flex items-center gap-2 text-zinc-100 font-mono font-semibold tracking-tight text-sm hover:text-white transition-colors focus:outline-none focus-visible:ring-1 focus-visible:ring-zinc-400 rounded px-1"
          aria-label="PatchProof Home"
        >
          <span className="w-6 h-6 rounded bg-zinc-800 border border-zinc-700 flex items-center justify-center text-zinc-200">
            <Shield className="w-3.5 h-3.5 text-emerald-400" />
          </span>
          <span>PATCHPROOF</span>
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden md:flex items-center gap-6 text-xs font-mono text-zinc-400">
          {navLinks.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`transition-colors hover:text-zinc-100 ${
                  isActive ? "text-zinc-100 font-medium" : "text-zinc-400"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        {/* Desktop CTAs */}
        <div className="hidden md:flex items-center gap-3">
          <Link
            href="/jobs"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-mono font-semibold transition-colors shadow-sm"
          >
            Launch Console <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        {/* Mobile Hamburger Button */}
        <div className="flex items-center gap-2 md:hidden">
          <Link
            href="/jobs"
            className="px-2.5 py-1 rounded bg-zinc-100 text-zinc-950 text-xs font-mono font-semibold"
          >
            Console
          </Link>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-1.5 rounded border border-zinc-800 bg-zinc-900 text-zinc-400 hover:text-white transition-colors"
            aria-label={mobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-border-subtle bg-surface-300 px-4 py-5 space-y-4 font-mono text-xs">
          <nav className="flex flex-col space-y-3">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`py-1 transition-colors ${
                  pathname === link.href ? "text-zinc-100 font-semibold" : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                {link.label}
              </Link>
            ))}
          </nav>

          <div className="pt-3 border-t border-border-subtle flex flex-col gap-2">
            <Link
              href="/jobs"
              className="w-full text-center py-2 rounded bg-zinc-100 text-zinc-950 font-semibold"
            >
              Open Security Console
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
