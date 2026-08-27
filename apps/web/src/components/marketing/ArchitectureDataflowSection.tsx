"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight, Code2, Cpu, FileCheck2, GitPullRequest, KeyRound, ShieldCheck } from "lucide-react";
import { useScrollReveal } from "@/hooks/useScrollReveal";

interface Stage {
  number: string;
  name: string;
  badge: string;
  summary: string;
  annotations: string[];
}

const STAGES: Stage[] = [
  {
    number: "01",
    name: "DETECT",
    badge: "WEBHOOK / AST",
    summary:
      "SAST alerts arrive via webhook with exact AST coordinates, CWE classification, and rule identifiers.",
    annotations: ["Webhook Signature: HMAC-SHA256", "AST Coordinate Mapping", "CWE Classification"],
  },
  {
    number: "02",
    name: "PATCH",
    badge: "TREE-SITTER",
    summary:
      "Tree-sitter isolates vulnerable AST nodes and synthesizes a strictly bounded syntactic replacement.",
    annotations: ["Tree-sitter AST Parse", "Syntax Diff Bounding", "Escape Isolation Guard"],
  },
  {
    number: "03",
    name: "VERIFY",
    badge: "gVisor 0-EGRESS",
    summary:
      "Patch executes in a 0-egress gVisor sandbox. Regression tests and Semgrep security re-scans must pass.",
    annotations: ["Kernel: gVisor runsc", "Network Egress: 0 Bytes", "Pytest Suite & Semgrep Rescan"],
  },
  {
    number: "04",
    name: "WRITE",
    badge: "ED25519 SEALED",
    summary:
      "Ed25519-signed evidence bundle is sealed. The authorized, tamper-proof PR is published to GitHub.",
    annotations: ["RFC 8032 Signature", "Canonical SHA-256 Digest", "Authorized GitHub PR"],
  },
];

export function ArchitectureDataflowSection() {
  const { ref, isRevealed } = useScrollReveal({ threshold: 0.1 });
  
  return (
    <div ref={ref} className="py-10 lg:py-12 w-full overflow-hidden">
      <div className={`max-w-[1600px] mx-auto px-6 sm:px-10 lg:px-16 xl:px-24 space-y-12 lg:space-y-16 transition-all duration-1000 ${isRevealed ? "opacity-100 translate-y-0" : "opacity-0 translate-y-12"}`}>

        {/* ── SECTION HEADER ── */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 max-w-4xl">
          <div className="space-y-4">
            <p className="text-sm font-mono uppercase tracking-[0.2em] text-zinc-500 font-semibold">
              Deterministic Architecture
            </p>
            <h2
              className="font-black tracking-tight text-zinc-100 font-sans leading-[0.95]"
              style={{ fontSize: "clamp(2.8rem, 5vw, 5rem)" }}
            >
              Four deterministic stages.
              <br />
              <span className="text-zinc-500">Zero trust assumptions.</span>
            </h2>
          </div>

          <Link
            href="/how-it-works"
            className="text-sm font-sans text-zinc-500 hover:text-zinc-300 inline-flex items-center gap-2 transition-colors self-start md:self-auto font-medium shrink-0"
          >
            Full technical specification <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* ── CONTINUOUS ARCHITECTURAL DATA-FLOW LINE ── */}
        <div className="hidden lg:block relative">
          {/* Continuous Flow Header Bar - No Container Border */}
          <div className="flex items-center justify-between font-mono text-[11px] text-zinc-500 tracking-wider uppercase border-b border-zinc-800/70 pb-5 mb-16">
            <span>DATAFLOW BUS</span>
            <div className="flex items-center gap-4 text-emerald-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>ISOLATED PIPELINE: ACTIVE</span>
            </div>
            <span>ZERO UNVERIFIED WRITES</span>
          </div>

          {/* 4 Connected Stages with Continuous Rail */}
          <div className="grid grid-cols-4 gap-8 xl:gap-12 relative">
            {/* Massive physical horizontal connecting bus rail */}
            <div
              className={`absolute top-[40px] left-[-20vw] right-[-20vw] h-1.5 transition-all duration-[2000ms] delay-500 ease-out -z-0 pointer-events-none ${isRevealed ? "scale-x-100" : "scale-x-0"}`}
              style={{ transformOrigin: 'left' }}
              aria-hidden="true"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-cyan-900/40 via-emerald-500/80 to-cyan-900/40" />
              <div className="absolute inset-y-0 left-0 right-0 bg-gradient-to-r from-transparent via-white/40 to-transparent blur-sm mix-blend-overlay" />
              <div className="absolute inset-y-[-10px] left-0 right-0 bg-gradient-to-r from-transparent via-emerald-500/30 to-transparent blur-xl" />
            </div>

            {STAGES.map((stage, idx) => (
              <div 
                key={stage.number} 
                className={`relative z-10 space-y-8 transition-all duration-700 ease-out`}
                style={{ 
                  opacity: isRevealed ? 1 : 0, 
                  transform: isRevealed ? 'translateY(0)' : 'translateY(20px)',
                  transitionDelay: `${300 + (idx * 150)}ms` 
                }}
              >
                {/* Stage Header with Number & Intersecting Node */}
                <div className="flex flex-col items-start gap-4">
                  <div
                    className="font-black text-zinc-800 font-mono leading-none select-none relative"
                    style={{ fontSize: "clamp(4rem, 6vw, 6rem)", letterSpacing: "-0.05em" }}
                  >
                    {/* The glowing node intersecting the physical pipeline */}
                    <div className="absolute top-[20px] left-[-15px] w-4 h-4 bg-zinc-950 border-2 border-emerald-400 rotate-45 shadow-[0_0_15px_rgba(52,211,153,0.8)] z-20" />
                    <span className="opacity-40">{stage.number}</span>
                  </div>
                  <span className="px-0 py-1 border-b border-emerald-900/50 text-[10px] font-mono text-emerald-400 font-bold tracking-widest uppercase">
                    {stage.badge}
                  </span>
                </div>

                {/* Stage Name */}
                <div className="space-y-2 pt-2">
                  <h3 className="text-2xl font-black text-zinc-100 font-sans tracking-tight">
                    {stage.name}
                  </h3>
                  <p className="text-zinc-400 text-sm font-sans leading-relaxed">
                    {stage.summary}
                  </p>
                </div>

                {/* Technical Annotations */}
                <div className="space-y-1.5 pt-3 border-t border-zinc-800/60 font-mono text-[11px] text-zinc-500">
                  {stage.annotations.map((ann, aIdx) => (
                    <div key={aIdx} className="flex items-center gap-2">
                      <span className="w-1 h-1 rounded-full bg-emerald-500/70 shrink-0" />
                      <span className="truncate">{ann}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ── MOBILE / TABLET VIEW ── */}
        <div className="lg:hidden space-y-6 divide-y divide-zinc-800/40">
          {STAGES.map((stage) => (
            <div key={stage.number} className="pt-8 space-y-4">
              <div className="flex items-baseline justify-between">
                <div className="font-black text-zinc-800/80 font-mono text-5xl leading-none select-none">
                  {stage.number}
                </div>
                <span className="px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-[10px] font-mono text-emerald-400 font-bold">
                  {stage.badge}
                </span>
              </div>
              <h3 className="text-2xl font-black text-zinc-100 font-sans tracking-tight">
                {stage.name}
              </h3>
              <p className="text-zinc-400 text-sm font-sans leading-relaxed">
                {stage.summary}
              </p>
              <div className="space-y-1 pt-2 font-mono text-sm text-zinc-400">
                {stage.annotations.map((ann, aIdx) => (
                  <div key={aIdx} className="flex items-center gap-2">
                    <span className="w-1 h-1 rounded-full bg-emerald-500/70" />
                    <span>{ann}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

      </div>
    </div>
  );
}
