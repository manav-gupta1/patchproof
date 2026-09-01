"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight, Code2, Cpu, FileCheck2, GitPullRequest, ShieldCheck } from "lucide-react";
import { useScrollReveal } from "@/hooks/useScrollReveal";

interface Stage {
  number: string;
  name: string;
  badge: string;
  summary: string;
  annotations: string[];
  icon: React.ReactNode;
}

const STAGES: Stage[] = [
  {
    number: "01",
    name: "DETECT",
    badge: "WEBHOOK / AST",
    summary:
      "SAST alerts arrive via webhook with exact AST coordinates, CWE classification, and rule identifiers.",
    annotations: ["Webhook Signature: HMAC-SHA256", "AST Coordinate Mapping", "CWE Classification"],
    icon: <Code2 className="w-4 h-4" />,
  },
  {
    number: "02",
    name: "PATCH",
    badge: "SAFE PATCH AGENT",
    summary:
      "Tree-sitter isolates vulnerable AST nodes and synthesizes a strictly bounded syntactic replacement.",
    annotations: ["Tree-sitter AST Parse", "Syntax Diff Bounding", "Escape Isolation Guard"],
    icon: <Cpu className="w-4 h-4" />,
  },
  {
    number: "03",
    name: "VERIFY",
    badge: "ISOLATED VERIFY",
    summary:
      "Patch executes in a 0-egress gVisor sandbox. Regression tests and Semgrep security re-scans must pass.",
    annotations: ["Kernel: gVisor runsc", "Network Egress: 0 Bytes", "Pytest Suite & Semgrep Rescan"],
    icon: <ShieldCheck className="w-4 h-4" />,
  },
  {
    number: "04",
    name: "WRITE",
    badge: "PR CREATION",
    summary:
      "Ed25519-signed evidence bundle is sealed. The authorized, tamper-proof PR is published to GitHub.",
    annotations: ["RFC 8032 Signature", "Canonical SHA-256 Digest", "Authorized GitHub PR"],
    icon: <GitPullRequest className="w-4 h-4" />,
  },
];

export function ArchitectureDataflowSection() {
  const { ref, isRevealed } = useScrollReveal({ threshold: 0.1 });
  
  return (
    <div ref={ref} className="py-10 lg:py-16 w-full overflow-hidden">
      <div className={`max-w-[1600px] mx-auto px-6 sm:px-8 lg:px-12 space-y-12 lg:space-y-16 transition-all duration-1000 ${isRevealed ? "opacity-100 translate-y-0" : "opacity-0 translate-y-12"}`}>

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

        {/* ── PIPELINE CARDS ── */}
        <div className="flex flex-col lg:flex-row items-stretch gap-4 lg:gap-2 xl:gap-4 relative">
          {STAGES.map((stage, idx) => (
            <React.Fragment key={stage.number}>
              {/* Card */}
              <div 
                className="flex-1 bg-zinc-900/30 border border-zinc-800/60 p-6 lg:p-8 rounded-xl flex flex-col hover:bg-zinc-900/60 hover:border-zinc-700 transition-colors duration-300 group"
                style={{
                  transitionDelay: `${idx * 150}ms`
                }}
              >
                {/* Large Background-style Number, but constrained to top-left */}
                <div className="text-[64px] lg:text-[80px] font-black font-mono leading-[0.8] tracking-tighter text-zinc-100 mb-6 group-hover:text-white transition-colors duration-300 select-none">
                  {stage.number}
                </div>
                
                {/* Small Technical Label */}
                <div className="flex items-center gap-2.5 mb-4">
                  <div className="text-emerald-500/80 group-hover:text-emerald-400 transition-colors">
                    {stage.icon}
                  </div>
                  <span className="text-[10px] font-mono text-emerald-400 font-bold tracking-widest uppercase">
                    [{stage.badge}]
                  </span>
                </div>

                {/* Stage Title */}
                <h3 className="text-xl lg:text-2xl font-black text-zinc-100 font-sans tracking-tight mb-3 group-hover:text-white transition-colors">
                  {stage.name}
                </h3>

                {/* Description */}
                <p className="text-zinc-400 text-sm font-sans leading-relaxed mb-8 flex-1">
                  {stage.summary}
                </p>

                {/* Technical Details (Bullet points) */}
                <div className="space-y-2.5 pt-5 border-t border-zinc-800/40 font-mono text-[10px] text-zinc-500">
                  {stage.annotations.map((ann, aIdx) => (
                    <div key={aIdx} className="flex items-center gap-2.5">
                      <span className="w-1 h-1 rounded-full bg-zinc-700 shrink-0 group-hover:bg-emerald-500/60 transition-colors" />
                      <span className="truncate group-hover:text-zinc-400 transition-colors">{ann}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Arrow separator */}
              {idx < STAGES.length - 1 && (
                <div className="flex items-center justify-center py-2 lg:py-0 lg:px-1 xl:px-3 shrink-0" aria-hidden="true">
                  <div className="w-10 h-10 lg:w-12 lg:h-12 rounded-full border border-zinc-800 bg-zinc-900/50 flex items-center justify-center shadow-[0_0_15px_rgba(52,211,153,0.05)]">
                    <ArrowRight className="w-4 h-4 lg:w-5 lg:h-5 text-emerald-500/80 rotate-90 lg:rotate-0 opacity-70 animate-pulse" />
                  </div>
                </div>
              )}
            </React.Fragment>
          ))}
        </div>

        {/* ── SYSTEM RESULT BAR ── */}
        <div className="mt-8 lg:mt-12 border border-zinc-800/60 bg-zinc-900/30 rounded-xl p-6 lg:p-8 flex flex-col md:flex-row items-center justify-between gap-8 md:gap-4 transition-all hover:bg-zinc-900/50 hover:border-zinc-700/60">
          
          {/* Left: Summary */}
          <div className="flex flex-col items-center md:items-start text-center md:text-left">
            <span className="text-[10px] font-mono text-zinc-500 tracking-widest uppercase mb-1.5 flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              END-TO-END AUTOMATION
            </span>
            <span className="text-zinc-200 font-bold tracking-tight text-sm md:text-base">
              Detect → Patch → Verify → Write
            </span>
          </div>
          
          {/* Right: Metrics */}
          <div className="flex flex-wrap md:flex-nowrap items-center justify-center gap-8 lg:gap-16 w-full md:w-auto">
            <div className="flex flex-col items-center md:items-start">
              <span className="text-2xl lg:text-3xl font-black text-emerald-400 font-mono tracking-tight">&lt; 30s</span>
              <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest mt-1">Avg. Remediation</span>
            </div>
            
            <div className="hidden md:block w-px h-10 bg-zinc-800/60" />
            
            <div className="flex flex-col items-center md:items-start">
              <span className="text-2xl lg:text-3xl font-black text-zinc-100 font-mono tracking-tight">95%+</span>
              <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest mt-1">Safe Patch Success</span>
            </div>
            
            <div className="hidden md:block w-px h-10 bg-zinc-800/60" />
            
            <div className="flex flex-col items-center md:items-start">
              <span className="text-2xl lg:text-3xl font-black text-zinc-100 font-mono tracking-tight">100%</span>
              <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest mt-1">Audit Traceability</span>
            </div>
          </div>
          
        </div>

      </div>
    </div>
  );
}
