"use client";

import React from "react";
import Link from "next/link";
import { Shield, ExternalLink, Lock } from "lucide-react";

export function Footer() {
  return (
    <footer className="w-full border-t border-border-subtle bg-surface-400 mt-20 text-xs font-mono text-zinc-500">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-12">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 mb-12">
          {/* Brand Col */}
          <div className="col-span-2 space-y-3">
            <Link href="/" className="flex items-center gap-2 text-zinc-200 font-semibold tracking-tight">
              <span className="w-5 h-5 rounded bg-zinc-800 border border-zinc-700 flex items-center justify-center text-zinc-300">
                <Shield className="w-3 h-3 text-emerald-400" />
              </span>
              <span>PATCHPROOF</span>
            </Link>
            <p className="text-zinc-400 text-xs font-sans leading-relaxed max-w-sm">
              AI writes the patch. PatchProof verifies it in isolated gVisor sandboxes and seals Ed25519 cryptographic proof before authorizing repository writes.
            </p>
            <div className="inline-flex items-center gap-2 px-2 py-1 rounded bg-zinc-900 border border-zinc-800 text-[11px] text-zinc-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span>Core Invariant: 0 Unverified Writes</span>
            </div>
          </div>

          {/* Product Col */}
          <div className="space-y-2.5">
            <div className="text-[11px] font-semibold text-zinc-300 uppercase tracking-wider">Product</div>
            <ul className="space-y-1.5 text-zinc-400">
              <li>
                <Link href="/how-it-works" className="hover:text-zinc-200 transition-colors">
                  How It Works
                </Link>
              </li>
              <li>
                <Link href="/security" className="hover:text-zinc-200 transition-colors">
                  Security & Trust
                </Link>
              </li>
              <li>
                <Link href="/pricing" className="hover:text-zinc-200 transition-colors">
                  Pricing & Tiers
                </Link>
              </li>
              <li>
                <Link href="/jobs" className="hover:text-zinc-200 transition-colors">
                  Security Console
                </Link>
              </li>
            </ul>
          </div>

          {/* Documentation & Resources */}
          <div className="space-y-2.5">
            <div className="text-[11px] font-semibold text-zinc-300 uppercase tracking-wider">Resources</div>
            <ul className="space-y-1.5 text-zinc-400">
              <li>
                <Link href="/docs" className="hover:text-zinc-200 transition-colors">
                  Documentation
                </Link>
              </li>
              <li>
                <Link href="/faq" className="hover:text-zinc-200 transition-colors">
                  FAQ
                </Link>
              </li>
              <li>
                <Link href="/contact" className="hover:text-zinc-200 transition-colors">
                  Support & Contact
                </Link>
              </li>
              <li>
                <Link href="/settings" className="hover:text-zinc-200 transition-colors">
                  System Telemetry
                </Link>
              </li>
            </ul>
          </div>

          {/* Security & Legal */}
          <div className="space-y-2.5">
            <div className="text-[11px] font-semibold text-zinc-300 uppercase tracking-wider">Trust & Legal</div>
            <ul className="space-y-1.5 text-zinc-400">
              <li>
                <Link href="/privacy" className="hover:text-zinc-200 transition-colors">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="/terms" className="hover:text-zinc-200 transition-colors">
                  Terms of Service
                </Link>
              </li>
              <li>
                <span className="text-zinc-600 block">Ed25519 Standard</span>
              </li>
              <li>
                <span className="text-zinc-600 block">gVisor Sandbox</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-6 border-t border-border-subtle flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-[11px] text-zinc-500">
          <div>
            © {new Date().getFullYear()} PatchProof Technologies Inc. All rights reserved.
          </div>
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5 text-zinc-400">
              <Lock className="w-3 h-3 text-emerald-400" /> Fail-Closed Protection Active
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
