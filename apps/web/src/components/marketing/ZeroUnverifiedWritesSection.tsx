"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  ShieldAlert,
  ShieldCheck,
  Lock,
  Unlock,
  CheckCircle2,
  XCircle,
  ArrowRight,
  GitPullRequest,
  Cpu,
  FileCode,
  KeyRound,
  Terminal,
  AlertOctagon,
  Check,
  X,
} from "lucide-react";

export function ZeroUnverifiedWritesSection() {
  // Toggle between successful verified write and fail-closed blocked write
  const [simulationMode, setSimulationMode] = useState<"success" | "blocked">("success");

  return (
    <section className="py-24 border-t border-border-muted bg-surface-400 select-none">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 space-y-16">
        {/* ── SECTION HEADER: THE CORE INVARIANT ── */}
        <div className="space-y-4 max-w-3xl">
          <div className="inline-flex items-center gap-2 text-[11px] font-mono text-zinc-400 tracking-wider">
            <span className="px-1.5 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-300 font-semibold uppercase">
              Core Invariant // SEC-INV-001
            </span>
            <span className="text-zinc-600">/</span>
            <span className="text-emerald-400 font-mono">NON-NEGOTIABLE GUARANTEE</span>
          </div>

          <h2 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-zinc-100 font-sans leading-none">
            0 UNVERIFIED WRITES.
          </h2>

          <p className="text-zinc-300 text-base sm:text-lg font-sans leading-relaxed">
            No automated patch is allowed to write until its verification evidence has been produced, sandbox-tested, and cryptographically signed. The write gate is deterministic: fail-closed by default.
          </p>
        </div>

        {/* ── INVARIANT SIMULATOR & CONTROL SWITCH ── */}
        <div className="space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-border-subtle font-mono text-xs">
            <div className="flex items-center gap-2 text-zinc-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse-subtle" />
              <span>Simulate Architectural Boundary:</span>
            </div>

            <div className="inline-flex p-1 rounded bg-surface-300 border border-border-subtle">
              <button
                onClick={() => setSimulationMode("success")}
                className={`px-3 py-1.5 rounded transition-all duration-150 text-xs flex items-center gap-1.5 ${
                  simulationMode === "success"
                    ? "bg-zinc-800 text-emerald-300 font-semibold border border-zinc-700 shadow-sm ring-1 ring-emerald-500/20"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                Scenario A: All Gates Pass (Authorized)
              </button>

              <button
                onClick={() => setSimulationMode("blocked")}
                className={`px-3 py-1.5 rounded transition-all duration-150 text-xs flex items-center gap-1.5 ${
                  simulationMode === "blocked"
                    ? "bg-zinc-800 text-rose-300 font-semibold border border-zinc-700 shadow-sm ring-1 ring-rose-500/20"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                <XCircle className="w-3.5 h-3.5 text-rose-400" />
                Scenario B: Sandbox Test Fails (Write Blocked)
              </button>
            </div>
          </div>

          {/* ── 3-ZONE HIGH-CONTRAST WRITE GATE ARCHITECTURE ── */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 font-mono text-xs">
            {/* ── ZONE 1: UNVERIFIED PATCH (Speculative Candidate) ── */}
            <div className="lg:col-span-4 p-4 sm:p-5 rounded-md border border-border-subtle bg-surface-300 flex flex-col justify-between space-y-4 shadow-lg">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-zinc-500 uppercase tracking-wider">
                    Zone 01 // Ingestion
                  </span>
                  <span className="px-1.5 py-0.5 rounded bg-amber-950/60 border border-amber-800/80 text-amber-300 text-[10px] font-semibold">
                    UNVERIFIED CANDIDATE
                  </span>
                </div>

                <div>
                  <h3 className="text-xs font-bold text-zinc-200 font-sans">
                    Synthetic Patch Proposal
                  </h3>
                  <p className="text-[11px] text-zinc-400 mt-0.5 font-sans">
                    AI generated AST replacement node for CWE-89 vulnerability.
                  </p>
                </div>

                {/* Quarantined Code Box */}
                <div className="p-2.5 bg-zinc-950 rounded border border-zinc-800 text-[11px] space-y-1 overflow-x-auto text-zinc-400">
                  <div className="text-[10px] text-amber-400 flex items-center gap-1 font-bold">
                    <Lock className="w-3 h-3" /> QUARANTINED IN MEMORY
                  </div>
                  <div className="text-zinc-500 select-none text-[10px]"># app/auth/session.py</div>
                  <code className="text-zinc-300 block">
                    cursor.execute(&quot;...&quot;, (id,))
                  </code>
                </div>
              </div>

              <div className="pt-3 border-t border-border-subtle text-[11px] text-zinc-500 space-y-1.5">
                <div className="flex justify-between">
                  <span>GitHub Remote Write:</span>
                  <span className="text-rose-400 font-bold">DENIED (0 writes)</span>
                </div>
                <div className="flex justify-between">
                  <span>Network Access:</span>
                  <span className="text-zinc-400">0 Egress (Drop-All)</span>
                </div>
              </div>
            </div>

            {/* ── ZONE 2: THE 5 DETERMINISTIC VERIFICATION GATES ── */}
            <div className="lg:col-span-4 p-4 sm:p-5 rounded-md border border-border-subtle bg-surface-300 flex flex-col justify-between space-y-4 shadow-lg">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-zinc-500 uppercase tracking-wider">
                    Zone 02 // Verification Conduit
                  </span>
                  <span className={`text-[10px] font-bold ${
                    simulationMode === "success" ? "text-emerald-400" : "text-rose-400"
                  }`}>
                    {simulationMode === "success" ? "5/5 GATES PASSED" : "GATE 03 FAILED"}
                  </span>
                </div>

                <div>
                  <h3 className="text-xs font-bold text-zinc-200 font-sans">
                    Deterministic Isolation Gates
                  </h3>
                  <p className="text-[11px] text-zinc-400 mt-0.5 font-sans">
                    Sequential checks executed inside gVisor before cryptographic attest.
                  </p>
                </div>

                {/* Gate Checklist */}
                <div className="space-y-1.5 text-[11px]">
                  {/* Gate 1 */}
                  <div className="p-2 rounded bg-zinc-950/80 border border-zinc-800 flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <span className="w-4 h-4 rounded bg-emerald-950 border border-emerald-800 text-emerald-400 flex items-center justify-center text-[10px]">
                        ✓
                      </span>
                      <span className="text-zinc-300">01. AST Syntax Parse</span>
                    </span>
                    <span className="text-emerald-400 text-[10px]">VALID</span>
                  </div>

                  {/* Gate 2 */}
                  <div className="p-2 rounded bg-zinc-950/80 border border-zinc-800 flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <span className="w-4 h-4 rounded bg-emerald-950 border border-emerald-800 text-emerald-400 flex items-center justify-center text-[10px]">
                        ✓
                      </span>
                      <span className="text-zinc-300">02. gVisor 0-Egress Kernel</span>
                    </span>
                    <span className="text-emerald-400 text-[10px]">0 BYTES</span>
                  </div>

                  {/* Gate 3 */}
                  <div className={`p-2 rounded border flex items-center justify-between transition-colors duration-150 ${
                    simulationMode === "success"
                      ? "bg-zinc-950/80 border-zinc-800"
                      : "bg-rose-950/30 border-rose-800/80"
                  }`}>
                    <span className="flex items-center gap-2">
                      <span className={`w-4 h-4 rounded flex items-center justify-center text-[10px] ${
                        simulationMode === "success"
                          ? "bg-emerald-950 border border-emerald-800 text-emerald-400"
                          : "bg-rose-950 border border-rose-800 text-rose-400"
                      }`}>
                        {simulationMode === "success" ? "✓" : "✕"}
                      </span>
                      <span className={simulationMode === "success" ? "text-zinc-300" : "text-rose-200"}>
                        03. Test Suite & Re-scan
                      </span>
                    </span>
                    <span className={simulationMode === "success" ? "text-emerald-400 text-[10px]" : "text-rose-400 text-[10px] font-bold"}>
                      {simulationMode === "success" ? "48/48 PASS" : "REGRESSION FAILED"}
                    </span>
                  </div>

                  {/* Gate 4 */}
                  <div className={`p-2 rounded border flex items-center justify-between ${
                    simulationMode === "success"
                      ? "bg-zinc-950/80 border-zinc-800"
                      : "bg-zinc-950/40 border-zinc-900 opacity-60"
                  }`}>
                    <span className="flex items-center gap-2">
                      <span className={`w-4 h-4 rounded flex items-center justify-center text-[10px] ${
                        simulationMode === "success"
                          ? "bg-emerald-950 border border-emerald-800 text-emerald-400"
                          : "bg-zinc-900 border border-zinc-800 text-zinc-600"
                      }`}>
                        {simulationMode === "success" ? "✓" : "—"}
                      </span>
                      <span className="text-zinc-300">04. Policy Threshold</span>
                    </span>
                    <span className={simulationMode === "success" ? "text-emerald-400 text-[10px]" : "text-zinc-500 text-[10px]"}>
                      {simulationMode === "success" ? "HIGH / CRITICAL" : "SKIPPED"}
                    </span>
                  </div>

                  {/* Gate 5 */}
                  <div className={`p-2 rounded border flex items-center justify-between ${
                    simulationMode === "success"
                      ? "bg-zinc-950/80 border-zinc-800"
                      : "bg-zinc-950/40 border-zinc-900 opacity-60"
                  }`}>
                    <span className="flex items-center gap-2">
                      <span className={`w-4 h-4 rounded flex items-center justify-center text-[10px] ${
                        simulationMode === "success"
                          ? "bg-emerald-950 border border-emerald-800 text-emerald-400"
                          : "bg-zinc-900 border border-zinc-800 text-zinc-600"
                      }`}>
                        {simulationMode === "success" ? "✓" : "—"}
                      </span>
                      <span className="text-zinc-300">05. Ed25519 Signature</span>
                    </span>
                    <span className={simulationMode === "success" ? "text-emerald-400 text-[10px]" : "text-zinc-500 text-[10px]"}>
                      {simulationMode === "success" ? "SIGNED (RFC 8032)" : "NOT SIGNED"}
                    </span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-border-subtle text-[11px] text-zinc-500 flex justify-between">
                <span>Hardware Isolation:</span>
                <span className="text-zinc-300">gVisor User-Space runsc</span>
              </div>
            </div>

            {/* ── ZONE 3: THE WRITE GATE (Decisive Security Boundary) ── */}
            <div className={`lg:col-span-4 p-4 sm:p-5 rounded-md border flex flex-col justify-between space-y-4 shadow-xl transition-all duration-200 ${
              simulationMode === "success"
                ? "bg-surface-300 border-emerald-900/60 ring-1 ring-emerald-500/20"
                : "bg-rose-950/20 border-rose-900/80 ring-1 ring-rose-500/20"
            }`}>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-zinc-500 uppercase tracking-wider">
                    Zone 03 // Binary Write Gate
                  </span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    simulationMode === "success"
                      ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                      : "bg-rose-950 text-rose-300 border border-rose-800"
                  }`}>
                    {simulationMode === "success" ? "WRITE AUTHORIZED" : "FAIL-CLOSED ABORT"}
                  </span>
                </div>

                <div>
                  <h3 className="text-xs font-bold text-zinc-100 font-sans">
                    {simulationMode === "success" ? "PR Published to GitHub" : "Remote Write Permanently Blocked"}
                  </h3>
                  <p className="text-[11px] text-zinc-400 mt-0.5 font-sans">
                    {simulationMode === "success"
                      ? "Pull request opened with verified commit hash and attached cryptographic evidence bundle."
                      : "Invariant enforced: When test or verification fails, zero remote writes reach the repository."}
                  </p>
                </div>

                <div className={`p-3 rounded border space-y-1.5 ${
                  simulationMode === "success"
                    ? "bg-zinc-950 border-emerald-900/60 text-zinc-300"
                    : "bg-zinc-950 border-rose-900/60 text-rose-300"
                }`}>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-zinc-500">Repository Remote Token:</span>
                    <span className={simulationMode === "success" ? "text-emerald-400 font-bold" : "text-rose-400 font-bold"}>
                      {simulationMode === "success" ? "UNLOCKED (PR #42)" : "LOCKED (0 WRITES)"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-zinc-500">Cryptographic Seal:</span>
                    <span className={simulationMode === "success" ? "text-emerald-400" : "text-zinc-600"}>
                      {simulationMode === "success" ? "Ed25519 Attached" : "None Produced"}
                    </span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-border-subtle text-[11px] text-zinc-400">
                <span className="font-semibold text-zinc-200">Outcome: </span>
                {simulationMode === "success" ? (
                  <span className="text-emerald-400">Deterministic proof verified. PR published safely.</span>
                ) : (
                  <span className="text-rose-400">Unverified code rejected. Zero writes sent to GitHub.</span>
                )}
              </div>
            </div>
          </div>

          {/* ── ARCHITECTURAL INVARIANT COMPARISON LEDGER ── */}
          <div className="border border-border-subtle rounded-md bg-surface-300 overflow-hidden font-mono text-xs shadow-xl">
            <div className="px-4 py-2.5 bg-surface-400 border-b border-border-subtle flex items-center justify-between">
              <span className="text-[11px] font-semibold text-zinc-300 uppercase tracking-wider">
                System Invariant Comparison Ledger
              </span>
              <span className="text-[10px] text-zinc-500">Specification SEC-INV-001</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-border-subtle bg-zinc-950/60 text-[10px] text-zinc-500 uppercase tracking-wider">
                    <th className="py-2.5 px-4 font-semibold">Security Dimension</th>
                    <th className="py-2.5 px-4 font-semibold text-rose-400">Standard AI Tooling</th>
                    <th className="py-2.5 px-4 font-semibold text-emerald-400">PatchProof Enforced Invariant</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-subtle text-zinc-300">
                  <tr className="hover:bg-zinc-900/30 transition-colors">
                    <td className="py-3 px-4 font-semibold text-zinc-100">Write Authorization</td>
                    <td className="py-3 px-4 text-rose-300 font-sans text-xs">Speculative push or unchecked PR creation</td>
                    <td className="py-3 px-4 text-emerald-300 font-sans text-xs font-medium">Zero writes without 5/5 verified sandbox gates</td>
                  </tr>
                  <tr className="hover:bg-zinc-900/30 transition-colors">
                    <td className="py-3 px-4 font-semibold text-zinc-100">Execution Sandbox</td>
                    <td className="py-3 px-4 text-rose-300 font-sans text-xs">Unisolated host runners or open network access</td>
                    <td className="py-3 px-4 text-emerald-300 font-sans text-xs font-medium">gVisor user-space kernel with 0 network egress (drop-all)</td>
                  </tr>
                  <tr className="hover:bg-zinc-900/30 transition-colors">
                    <td className="py-3 px-4 font-semibold text-zinc-100">Evidence & Proof</td>
                    <td className="py-3 px-4 text-rose-300 font-sans text-xs">Unverifiable text assertions (&quot;looks good&quot;)</td>
                    <td className="py-3 px-4 text-emerald-300 font-sans text-xs font-medium">RFC 8032 Ed25519 cryptographic digital signature over SHA-256 evidence</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
