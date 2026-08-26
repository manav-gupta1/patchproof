"use client";

import React from "react";
import { ShieldCheck, Cpu, KeyRound, GitPullRequest, ArrowRight, Lock, CheckCircle2 } from "lucide-react";

export function ValuePropositionHero() {
  return (
    <div
      className="border border-border-subtle bg-surface-300 rounded-md p-6 sm:p-7 space-y-6"
      data-testid="value-prop-hero"
    >
      <div className="space-y-6">
        {/* Top Tagline & Badge */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded bg-zinc-900 border border-zinc-800 text-xs font-mono text-zinc-300">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span className="font-semibold text-zinc-200">Autonomous Security Remediation Engine</span>
          </div>

          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-950/50 border border-emerald-800 text-xs font-mono text-emerald-300">
            <Lock className="w-3 h-3 text-emerald-400" />
            <span>Zero-Write Security Invariant Enforced</span>
          </div>
        </div>

        {/* Headline & Description */}
        <div className="max-w-3xl space-y-2">
          <h2 className="text-xl sm:text-2xl lg:text-3xl font-bold text-zinc-100 tracking-tight leading-snug font-sans">
            Verify before you publish. Protect production automatically.
          </h2>
          <p className="text-xs sm:text-sm text-zinc-400 leading-relaxed font-sans">
            PatchProof automatically detects vulnerabilities, safely synthesizes AST patches, verifies them in isolated gVisor sandboxes, and publishes only cryptographically verified pull requests.
          </p>
        </div>

        {/* 4-Stage Verifiable Architecture Stepper */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-2 font-mono text-xs">
          {/* Step 1 */}
          <div className="p-3.5 rounded bg-zinc-900/60 border border-border-subtle flex items-start gap-3">
            <div className="w-7 h-7 rounded bg-zinc-900 border border-zinc-700 flex items-center justify-center text-zinc-300 font-mono text-xs font-bold shrink-0">
              01
            </div>
            <div>
              <div className="text-xs font-semibold text-zinc-200 font-sans">Webhook Ingestion</div>
              <div className="text-[11px] text-zinc-500 mt-0.5 font-mono">HMAC SHA-256 alerts</div>
            </div>
          </div>

          {/* Step 2 */}
          <div className="p-3.5 rounded bg-zinc-900/60 border border-border-subtle flex items-start gap-3">
            <div className="w-7 h-7 rounded bg-zinc-900 border border-zinc-700 flex items-center justify-center text-zinc-300 font-mono text-xs font-bold shrink-0">
              02
            </div>
            <div>
              <div className="text-xs font-semibold text-zinc-200 font-sans">Patch Synthesis</div>
              <div className="text-[11px] text-zinc-500 mt-0.5 font-mono">AST Tree-sitter delta</div>
            </div>
          </div>

          {/* Step 3 */}
          <div className="p-3.5 rounded bg-zinc-900/60 border border-border-subtle flex items-start gap-3">
            <div className="w-7 h-7 rounded bg-zinc-900 border border-zinc-700 flex items-center justify-center text-zinc-300 font-mono text-xs font-bold shrink-0">
              03
            </div>
            <div>
              <div className="text-xs font-semibold text-zinc-200 font-sans">gVisor Sandbox</div>
              <div className="text-[11px] text-zinc-500 mt-0.5 font-mono">0 network egress test</div>
            </div>
          </div>

          {/* Step 4 */}
          <div className="p-3.5 rounded bg-zinc-900/60 border border-border-subtle flex items-start gap-3">
            <div className="w-7 h-7 rounded bg-zinc-900 border border-zinc-700 flex items-center justify-center text-emerald-400 font-mono text-xs font-bold shrink-0">
              04
            </div>
            <div>
              <div className="text-xs font-semibold text-zinc-200 font-sans">Verified PR</div>
              <div className="text-[11px] text-zinc-500 mt-0.5 font-mono">Ed25519 signed proof</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
