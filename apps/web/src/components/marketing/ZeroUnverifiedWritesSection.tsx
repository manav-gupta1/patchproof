"use client";

import React from "react";
import { AlertOctagon, CheckCircle2, ShieldAlert, ShieldCheck } from "lucide-react";
import { useScrollReveal } from "@/hooks/useScrollReveal";

export function ZeroUnverifiedWritesSection() {
  const { ref, isRevealed } = useScrollReveal({ threshold: 0.1 });
  return (
    <div ref={ref} className="py-12 lg:py-16 w-full">
      <div className={`max-w-[1600px] mx-auto px-6 sm:px-10 lg:px-16 xl:px-24 space-y-16 lg:space-y-20 transition-all duration-1000 ${isRevealed ? "opacity-100 translate-y-0" : "opacity-0 translate-y-12"}`}>

        {/* ── SECTION HEADER ── */}
        <div className="max-w-3xl space-y-6">
          <p className="text-xs font-mono uppercase tracking-[0.2em] text-zinc-500 font-semibold">
            The Structural Flaw
          </p>
          <h2
            className="font-black tracking-tight text-zinc-100 font-sans leading-[0.95]"
            style={{ fontSize: "clamp(2.6rem, 4.5vw, 4.8rem)" }}
          >
            AI can write code.
            <br />
            <span className="text-zinc-500">
              Nothing proves it&apos;s safe.
            </span>
          </h2>
          <p className="text-zinc-400 text-base sm:text-lg font-sans leading-relaxed max-w-[680px]">
            Standard automated tools push speculative AI patches directly to your
            default branch. No sandbox containment. No test execution. No cryptographic
            attestation. You merge on trust and discover regressions in production.
          </p>
        </div>

        {/* ── LARGE HORIZONTAL DATAFLOW MECHANISM ── */}
        <div className="relative">
          {/* Depth Masking Background */}
          <div className="absolute inset-[-10%] bg-[radial-gradient(ellipse_at_center,var(--graphite-900)_0%,transparent_70%)] pointer-events-none -z-10" aria-hidden="true" />
          
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-16 xl:gap-24 relative z-10">
            
            {/* Subtle vertical divider between the two systems on desktop */}
            <div className="hidden xl:block absolute left-1/2 top-0 bottom-0 w-[1px] bg-gradient-to-b from-transparent via-zinc-800/50 to-transparent -translate-x-1/2" />

          {/* 1. TRADITIONAL UNVERIFIED PATH */}
          <div className="space-y-12">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-rose-900/30 pb-5">
              <div className="flex items-center gap-3">
                <ShieldAlert className="w-6 h-6 text-rose-500" />
                <span className="text-xs font-mono uppercase tracking-[0.2em] text-rose-500 font-bold">
                  Traditional Automated Patching
                </span>
              </div>
              <span className="text-xs font-mono text-rose-400/70 font-semibold tracking-wider">
                UNVERIFIED / FAIL-OPEN
              </span>
            </div>

            {/* Horizontal flow line */}
            <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
              {/* Step 1: AI Prompt */}
              <div className="md:col-span-4 space-y-3">
                <div className="text-xs font-mono text-zinc-500 uppercase tracking-wider">01. INGESTION</div>
                <div className="text-xl font-bold font-sans text-zinc-200">AI Model Output</div>
                <p className="text-xs font-sans text-zinc-500 leading-relaxed">Speculative LLM patch proposal based on prompt context.</p>
              </div>

              {/* Arrow connector */}
              <div className="md:col-span-1 flex justify-center text-rose-500/40 text-2xl font-mono select-none">
                →
              </div>

              {/* Step 2: Unchecked Write Failure Node */}
              <div className="md:col-span-4 border-l-2 border-rose-800/50 pl-5 space-y-2 relative">
                <div className="absolute -left-[3px] top-0 bottom-0 w-[2px] bg-rose-500/20 blur-sm" />
                <div className="flex items-center gap-2 text-rose-400 font-mono text-xs font-bold uppercase tracking-wider">
                  <AlertOctagon className="w-4 h-4 text-rose-400 shrink-0" />
                  Blind Write Boundary
                </div>
                <p className="text-xs font-sans text-rose-200/90 leading-relaxed">
                  No AST syntax check. No isolated container. 0 test runs. Code written directly to GitHub on probabilistic confidence.
                </p>
              </div>

              {/* Arrow connector */}
              <div className="md:col-span-1 flex justify-center text-rose-500/40 text-2xl font-mono select-none">
                →
              </div>

              {/* Step 3: Production Merge */}
              <div className="md:col-span-4 space-y-3">
                <div className="text-xs font-mono text-rose-500/70 uppercase tracking-wider">02. OUTCOME</div>
                <div className="text-xl font-bold font-sans text-rose-400">Trust After Merger</div>
                <p className="text-xs font-sans text-zinc-500 leading-relaxed">Syntax errors and security regressions discovered by end users in production.</p>
              </div>
            </div>
          </div>

          {/* 2. PATCHPROOF DETERMINISTIC PATH */}
          <div className="space-y-12">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-emerald-900/30 pb-5">
              <div className="flex items-center gap-3">
                <ShieldCheck className="w-6 h-6 text-emerald-400" />
                <span className="text-xs font-mono uppercase tracking-[0.2em] text-emerald-400 font-bold">
                  PatchProof Architecture
                </span>
              </div>
              <span className="text-xs font-mono text-emerald-400/70 font-semibold tracking-wider">
                ZERO UNVERIFIED WRITES / FAIL-CLOSED
              </span>
            </div>

            {/* Vertical flow line with 5 concrete gates to contrast with horizontal left side */}
            <div className="flex flex-col gap-8 relative pl-8 before:absolute before:left-0 before:top-2 before:bottom-2 before:w-[1px] before:bg-gradient-to-b before:from-emerald-900/50 before:via-emerald-500/30 before:to-transparent">
              {/* Gate 1: AST Coordinate Filter */}
              <div className="relative space-y-2">
                <div className="absolute -left-[32.5px] top-1 w-2 h-2 rounded-full bg-emerald-950 border border-emerald-500/50" />
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-emerald-500 tracking-widest">[01] AST_GATE</span>
                </div>
                <div className="text-base font-bold font-sans text-zinc-100">Tree-sitter Parse</div>
                <p className="text-xs font-sans text-zinc-400 leading-relaxed">
                  Validates syntax tree delta. Bounded strictly to vulnerable node coordinates. Escapes blocked.
                </p>
              </div>

              {/* Gate 2: gVisor Sandbox */}
              <div className="relative space-y-2">
                <div className="absolute -left-[32.5px] top-1 w-2 h-2 rounded-full bg-emerald-950 border border-emerald-500/50" />
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-emerald-500 tracking-widest">[02] ISO_SANDBOX</span>
                </div>
                <div className="text-base font-bold font-sans text-zinc-100">gVisor Isolation</div>
                <p className="text-xs font-sans text-zinc-400 leading-relaxed">
                  Executes inside isolated runsc kernel sandbox. Non-root user with 0 network egress.
                </p>
              </div>

              {/* Gate 3: Tests & Rescan */}
              <div className="relative space-y-2">
                <div className="absolute -left-[32.5px] top-1 w-2 h-2 rounded-full bg-emerald-950 border border-emerald-500/50" />
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-emerald-500 tracking-widest">[03] RESCAN_TEST</span>
                </div>
                <div className="text-base font-bold font-sans text-zinc-100">Regression + Rescan</div>
                <p className="text-xs font-sans text-zinc-400 leading-relaxed">
                  Runs full pytest suite and Semgrep re-scan. Confirms vulnerability elimination with zero regressions.
                </p>
              </div>

              {/* Gate 4: Policy Engine */}
              <div className="relative space-y-2">
                <div className="absolute -left-[32.5px] top-1 w-2 h-2 rounded-full bg-emerald-950 border border-emerald-500/50" />
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-emerald-500 tracking-widest">[04] POLICY_EVAL</span>
                </div>
                <div className="text-base font-bold font-sans text-zinc-100">Rule Evaluation</div>
                <p className="text-xs font-sans text-zinc-400 leading-relaxed">
                  Evaluates repository policy thresholds, branch rules, and severity levels. Fails closed on denial.
                </p>
              </div>

              {/* Gate 5: Ed25519 Cryptographic Proof */}
              <div className="relative space-y-2 border-l border-emerald-400/30 pl-4 py-1 -ml-4">
                <div className="absolute -left-[20.5px] top-2 w-3 h-3 bg-emerald-400 rotate-45 shadow-[0_0_10px_rgba(52,211,153,0.6)]" />
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-emerald-300 tracking-widest font-bold">AUTHORIZED_WRITE</span>
                </div>
                <div className="text-base font-bold font-sans text-emerald-300">Ed25519 Signed PR</div>
                <p className="text-xs font-sans text-emerald-400/70 leading-relaxed">
                  Canonical SHA-256 evidence sealed with RFC 8032 digital signature before GitHub PR is created.
                </p>
              </div>
            </div>
          </div>

          </div>
        </div>

      </div>
    </div>
  );
}
