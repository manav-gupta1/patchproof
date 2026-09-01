"use client";

import React from "react";
import { Shield, Lock, CheckCircle2, FileCode2, Terminal, AlertTriangle, KeyRound, GitPullRequest } from "lucide-react";
import { useScrollReveal } from "@/hooks/useScrollReveal";

export function SecurityArchitectureSection() {
  const { ref, isRevealed } = useScrollReveal({ threshold: 0.1 });
  const gates = [
    {
      id: "01",
      title: "Untrusted AI Proposal",
      layer: "INGESTION BOUNDARY",
      icon: <AlertTriangle className="w-5 h-5 text-amber-400" />,
      desc: "LLM patch output is treated as strictly untrusted user input. It has zero filesystem or network privileges.",
      telemetry: "STATUS: UNTRUSTED / TAINTED",
      badgeColor: "border-amber-900/60 bg-amber-950/30 text-amber-400",
    },
    {
      id: "02",
      title: "AST Coordinate Boundary",
      layer: "SYNTAX FILTER",
      icon: <FileCode2 className="w-5 h-5 text-emerald-400" />,
      desc: "Tree-sitter parses the target syntax tree. Diff is constrained to the exact vulnerable AST node range. Lateral file rewrites fail.",
      telemetry: "SCOPE: STRICT NODE RANGE",
      badgeColor: "border-zinc-800 bg-zinc-900 text-zinc-300",
    },
    {
      id: "03",
      title: "gVisor 0-Egress Sandbox",
      layer: "ISOLATION CONTAINER",
      icon: <Terminal className="w-5 h-5 text-emerald-400" />,
      desc: "Executes inside gVisor runsc kernel sandbox. 512MB RAM cap, non-root uid 10001, iptables DROP-ALL on all egress.",
      telemetry: "NET: 0 BYTES / UID: 10001",
      badgeColor: "border-emerald-900/60 bg-emerald-950/40 text-emerald-300",
    },
    {
      id: "04",
      title: "Regression & Semgrep Rescan",
      layer: "VERIFICATION GATE",
      icon: <CheckCircle2 className="w-5 h-5 text-emerald-400" />,
      desc: "Runs repository pytest test suite and re-scans with Semgrep rules to verify vulnerability elimination with zero regressions.",
      telemetry: "TESTS: PASS / FINDINGS: 0",
      badgeColor: "border-zinc-800 bg-zinc-900 text-zinc-300",
    },
    {
      id: "05",
      title: "Repository Policy Engine",
      layer: "GOVERNANCE",
      icon: <Lock className="w-5 h-5 text-emerald-400" />,
      desc: "Evaluates repository severity thresholds, branch protections, and auto-remediate flags. Fails closed on any policy denial.",
      telemetry: "POLICY: ALLOWED",
      badgeColor: "border-zinc-800 bg-zinc-900 text-zinc-300",
    },
    {
      id: "06",
      title: "Ed25519 Sealed Attestation",
      layer: "CRYPTOGRAPHY",
      icon: <KeyRound className="w-5 h-5 text-emerald-400" />,
      desc: "Canonical SHA-256 digest sealed with RFC 8032 Ed25519 digital signature. Tamper-evident evidence manifest.",
      telemetry: "SIG: RFC 8032 ED25519",
      badgeColor: "border-emerald-900/60 bg-emerald-950/40 text-emerald-300",
    },
    {
      id: "07",
      title: "Authorized GitHub PR",
      layer: "WRITE BOUNDARY",
      icon: <GitPullRequest className="w-5 h-5 text-emerald-400" />,
      desc: "Only after all 6 verification gates pass and the cryptographic signature is verified does the write gate unlock.",
      telemetry: "PR: PUBLISHED WITH PROOF",
      badgeColor: "border-emerald-800/60 bg-emerald-950/50 text-emerald-300",
    },
  ];

  return (
    <div ref={ref} className="py-12 lg:py-16 w-full overflow-hidden">
      <div className={`max-w-[1600px] mx-auto px-6 sm:px-8 lg:px-12 space-y-12 lg:space-y-16 transition-all duration-1000 ${isRevealed ? "opacity-100 translate-y-0" : "opacity-0 translate-y-12"}`}>

        {/* ── SECTION HEADER ── */}
        <div className="max-w-3xl space-y-6">
          <p className="text-sm font-mono uppercase tracking-[0.2em] text-zinc-500 font-semibold">
            Security Model & Boundaries
          </p>
          <h2
            className="font-black tracking-tight text-zinc-100 font-sans leading-[0.95]"
            style={{ fontSize: "clamp(2.6rem, 4.5vw, 4.8rem)" }}
          >
            The Fail-Closed
            <br />
            <span className="text-zinc-500">Security Architecture.</span>
          </h2>
          <p className="text-zinc-400 text-base sm:text-lg font-sans leading-relaxed max-w-[650px]">
            Zero unverified writes to GitHub. Every patch must traverse 7 deterministic,
            isolated security boundaries. If any stage encounters an error, execution
            halts immediately.
          </p>
        </div>

        {/* ── NESTED SPATIAL CONTAINMENT DIAGRAM ── */}
        <div className="relative w-full max-w-[1100px] mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-zinc-800/70 pb-5 mb-10 font-mono text-[11px] text-zinc-500 uppercase tracking-wider">
            <span>ISOLATION CONTAINMENT MODEL</span>
            <span className="text-emerald-400 font-bold flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              FAIL-CLOSED INVARIANT: ACTIVE
            </span>
          </div>

          <div className="relative">
            {gates.map((gate, idx) => {
              // Calculate nesting dimensions: each layer is smaller than the last
              // and positioned progressively downwards/inwards.
              const padding = 24 - (idx * 2);
              const zIndex = 10 + idx;
              const delay = idx * 100;
              
              // We alternate alignment slightly to give an asymmetrical technical feel
              const isEven = idx % 2 === 0;

              return (
                <div 
                  key={gate.id}
                  className={`relative w-full transition-all duration-[800ms] ease-out border-t border-l border-r rounded-t-xl`}
                  style={{
                    paddingTop: `${Math.max(16, padding)}px`,
                    paddingLeft: `${Math.max(16, padding)}px`,
                    paddingRight: `${Math.max(16, padding)}px`,
                    marginTop: idx === 0 ? '0' : `-${padding/2}px`,
                    borderColor: gate.badgeColor.split(' ')[0].replace('border-', 'rgba(255,255,255,0.1)'), // fallback if complex
                    background: `linear-gradient(to bottom, ${gate.badgeColor.includes('amber') ? 'rgba(251,191,36,0.03)' : gate.badgeColor.includes('emerald') ? 'rgba(16,185,129,0.02)' : 'rgba(255,255,255,0.01)'}, transparent)`,
                    zIndex: zIndex,
                    opacity: isRevealed ? 1 : 0,
                    transform: isRevealed ? 'translateY(0)' : 'translateY(15px)',
                    transitionDelay: `${delay}ms`
                  }}
                >
                  <div className={`flex flex-col md:flex-row gap-6 items-start md:items-center p-6 bg-zinc-950/80 backdrop-blur-sm border rounded-xl shadow-2xl ${gate.badgeColor.split(' ')[0]}`}>
                    {/* Gate Number & Icon */}
                    <div className="flex items-center gap-4 min-w-[280px]">
                      <span className="text-sm font-mono font-bold text-zinc-500 w-6 tabular-nums">{gate.id}</span>
                      <div className="p-2.5 rounded-lg bg-zinc-900 border border-zinc-800/80 shadow-inner">
                        {gate.icon}
                      </div>
                      <div>
                        <div className="text-[10px] font-mono uppercase tracking-widest text-zinc-500 mb-1">{gate.layer}</div>
                        <div className="text-base font-bold font-sans text-zinc-100">{gate.title}</div>
                      </div>
                    </div>

                    {/* Description */}
                    <div className="flex-1 text-sm font-sans text-zinc-400 leading-relaxed pr-4">
                      {gate.desc}
                    </div>

                    {/* Telemetry Badge */}
                    <div className="shrink-0 flex md:justify-end">
                      <span className={`px-3 py-1.5 rounded-md border text-[10px] font-mono font-bold tracking-widest ${gate.badgeColor}`}>
                        {gate.telemetry}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
            
            {/* The final terminating block at the bottom */}
            <div 
              className={`relative h-4 w-full border-b border-l border-r rounded-b-xl transition-all duration-1000 ease-out`}
              style={{
                borderColor: gates[gates.length-1].badgeColor.split(' ')[0],
                opacity: isRevealed ? 1 : 0,
                transitionDelay: `${gates.length * 100}ms`
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
