"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  ShieldCheck,
  Lock,
  ArrowRight,
  FileCode,
  Terminal,
  CheckCircle2,
  Cpu,
  KeyRound,
  GitPullRequest,
  Check,
  Copy,
  ExternalLink,
  ChevronRight,
  Shield,
  Zap,
} from "lucide-react";

type ControlPlaneTab = "diff" | "sandbox" | "crypto" | "pr";

interface PipelineNode {
  id: string;
  number: string;
  label: string;
  sublabel: string;
  status: "completed" | "active" | "queued";
  tab: ControlPlaneTab;
}

export function HeroVerificationControlPlane() {
  const [activeTab, setActiveTab] = useState<ControlPlaneTab>("diff");
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const pipelineNodes: PipelineNode[] = [
    {
      id: "received",
      number: "01",
      label: "PATCH RECEIVED",
      sublabel: "Alert CWE-89 parsed",
      status: "completed",
      tab: "diff",
    },
    {
      id: "generated",
      number: "02",
      label: "PATCH GENERATED",
      sublabel: "AST Tree-sitter delta",
      status: "completed",
      tab: "diff",
    },
    {
      id: "sandbox",
      number: "03",
      label: "gVisor SANDBOX",
      sublabel: "0-egress user kernel",
      status: "completed",
      tab: "sandbox",
    },
    {
      id: "tests",
      number: "04",
      label: "48 TESTS PASSED",
      sublabel: "0 regression findings",
      status: "completed",
      tab: "sandbox",
    },
    {
      id: "policy",
      number: "05",
      label: "POLICY VERIFIED",
      sublabel: "Severity: HIGH (allow)",
      status: "completed",
      tab: "sandbox",
    },
    {
      id: "evidence",
      number: "06",
      label: "EVIDENCE SEALED",
      sublabel: "Canonical SHA-256",
      status: "completed",
      tab: "crypto",
    },
    {
      id: "ed25519",
      number: "07",
      label: "ED25519 VERIFIED",
      sublabel: "RFC 8032 signature",
      status: "completed",
      tab: "crypto",
    },
    {
      id: "write",
      number: "08",
      label: "WRITE AUTHORIZED",
      sublabel: "PR #42 published",
      status: "completed",
      tab: "pr",
    },
  ];

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return (
    <section className="pt-12 sm:pt-16 pb-20 max-w-6xl mx-auto px-4 sm:px-6 select-none">
      {/* ── 1. ASYMMETRIC COMMAND HEADLINE & SECURITY HUD ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left 7 Cols: Monumental Statement & Core Guarantee */}
        <div className="lg:col-span-7 space-y-6">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded bg-zinc-900 border border-zinc-800 text-[11px] font-mono text-zinc-300">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse-subtle" />
            <span className="text-zinc-400 uppercase tracking-wider font-semibold">
              Zero-Write Security Boundary
            </span>
            <span className="text-zinc-600">/</span>
            <span className="text-emerald-400 font-medium">Fail-Closed Invariant Active</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-zinc-100 font-sans leading-[1.05]">
            EVERY PATCH MUST{" "}
            <span className="text-emerald-400 underline decoration-emerald-500/40 underline-offset-8">
              PROVE ITSELF.
            </span>
          </h1>

          <p className="text-zinc-300 text-base sm:text-lg font-sans leading-relaxed max-w-xl">
            AI writes the patch. PatchProof verifies it. Every patch must pass isolated gVisor sandboxes, regression test suites, and Ed25519 cryptographic sealing before any write reaches GitHub.
          </p>

          <div className="pt-2 flex flex-wrap items-center gap-3 font-mono text-xs">
            <a
              href="#console"
              className="px-5 py-2.5 rounded bg-zinc-100 hover:bg-white text-zinc-950 font-semibold transition-all duration-150 shadow-sm inline-flex items-center gap-1.5 focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none"
            >
              Launch Console <ArrowRight className="w-3.5 h-3.5" />
            </a>
            <Link
              href="/security"
              className="px-4 py-2.5 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-200 transition-all duration-150 focus-visible:ring-1 focus-visible:ring-zinc-400 focus-visible:outline-none"
            >
              Inspect Security Architecture
            </Link>
            <Link
              href="/docs"
              className="px-3 py-2.5 text-zinc-400 hover:text-zinc-200 transition-all duration-150 inline-flex items-center gap-1"
            >
              Documentation <ChevronRight className="w-3 h-3" />
            </Link>
          </div>
        </div>

        {/* Right 5 Cols: Authoritative System Specifications Panel */}
        <div className="lg:col-span-5 rounded-md border border-border-subtle bg-surface-300 p-4 font-mono text-xs space-y-3 shadow-lg">
          <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
            <span className="text-zinc-400 font-semibold text-[11px] uppercase tracking-wider">
              System Invariants
            </span>
            <span className="text-emerald-400 text-[10px] font-bold">
              FAIL-CLOSED
            </span>
          </div>

          <div className="space-y-1.5 text-[11px]">
            <div className="flex items-center justify-between p-2 rounded bg-zinc-950/70 border border-border-subtle">
              <span className="text-zinc-500">Sandbox Isolation</span>
              <span className="text-zinc-200 font-medium">gVisor runsc (user-space)</span>
            </div>
            <div className="flex items-center justify-between p-2 rounded bg-zinc-950/70 border border-border-subtle">
              <span className="text-zinc-500">Network Outbound</span>
              <span className="text-emerald-400 font-medium">0 Bytes (Drop-All)</span>
            </div>
            <div className="flex items-center justify-between p-2 rounded bg-zinc-950/70 border border-border-subtle">
              <span className="text-zinc-500">Attestation Seal</span>
              <span className="text-zinc-200 font-medium">RFC 8032 Ed25519</span>
            </div>
            <div className="flex items-center justify-between p-2 rounded bg-zinc-950/70 border border-border-subtle">
              <span className="text-zinc-500">Unverified Writes</span>
              <span className="text-rose-400 font-medium">0 Permitted</span>
            </div>
          </div>

          <div className="pt-1.5 border-t border-border-subtle flex items-center justify-between text-[10px] text-zinc-500">
            <span>Deterministic gate evaluator</span>
            <span className="text-emerald-400">5/5 Verification Gates</span>
          </div>
        </div>
      </div>

      {/* ── 2. PRODUCT VERIFICATION CONTROL PLANE ── */}
      <div className="mt-12 rounded-md border border-border-muted bg-surface-300 shadow-2xl overflow-hidden font-mono text-xs">
        {/* Control Plane Header */}
        <div className="px-4 sm:px-5 py-3 bg-surface-400 border-b border-border-subtle flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse-subtle" />
              <span className="text-[11px] font-semibold text-zinc-200 tracking-tight">
                VERIFICATION RUN #8904-SEC
              </span>
            </div>
            <span className="text-zinc-600 hidden sm:inline">|</span>
            <span className="text-zinc-400 text-[11px] hidden sm:inline">
              Target: <strong className="text-zinc-200">octocat/auth-service</strong> @ <span className="text-zinc-400">7f9a3b2</span>
            </span>
          </div>

          <div className="flex items-center gap-2 text-[11px]">
            <span className="px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-400 text-[10px]">
              CWE-89 SQL Injection
            </span>
            <span className="px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-800 text-emerald-300 text-[10px] font-semibold flex items-center gap-1 transition-colors duration-150">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse-subtle" />
              GATE STATUS: AUTHORIZED (5/5 PASS)
            </span>
          </div>
        </div>

        {/* 8-Stage Sequential State Pipeline Conduit */}
        <div className="p-3 sm:p-4 bg-zinc-950/60 border-b border-border-subtle overflow-x-auto">
          <div className="flex items-center justify-between min-w-[760px] gap-1">
            {pipelineNodes.map((node, index) => {
              const isSelected = activeTab === node.tab;

              return (
                <React.Fragment key={node.id}>
                  <button
                    onClick={() => setActiveTab(node.tab)}
                    className={`flex-1 p-2 rounded text-left transition-all duration-150 group ${
                      isSelected
                        ? "bg-zinc-900 border border-zinc-700 shadow-sm ring-1 ring-emerald-500/20"
                        : "bg-surface-300/60 hover:bg-zinc-900/60 border border-border-subtle"
                    }`}
                    title={`Inspect ${node.label}`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] text-zinc-500 font-mono">
                        {node.number}
                      </span>
                      <span className="w-3.5 h-3.5 rounded-full bg-emerald-950 border border-emerald-800 flex items-center justify-center text-emerald-400 text-[9px] transition-colors duration-150">
                        ✓
                      </span>
                    </div>
                    <div
                      className={`text-[11px] font-bold tracking-tight truncate transition-colors duration-150 ${
                        isSelected ? "text-emerald-300" : "text-zinc-200 group-hover:text-zinc-100"
                      }`}
                    >
                      {node.label}
                    </div>
                    <div className="text-[9px] text-zinc-500 truncate mt-0.5 font-mono">
                      {node.sublabel}
                    </div>
                  </button>

                  {index < pipelineNodes.length - 1 && (
                    <div className="text-zinc-700 font-mono text-xs px-0.5 select-none shrink-0 group-hover:text-zinc-500 transition-colors">
                      →
                    </div>
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>

        {/* Interactive Verification Detail Pane */}
        <div className="p-4 sm:p-5">
          {/* Sub-navigation tabs */}
          <div className="flex items-center justify-between pb-3 mb-4 border-b border-border-subtle">
            <div className="flex items-center gap-1 overflow-x-auto">
              <button
                onClick={() => setActiveTab("diff")}
                className={`px-3 py-1.5 rounded text-xs transition-all duration-150 flex items-center gap-1.5 ${
                  activeTab === "diff"
                    ? "bg-zinc-800 text-zinc-100 font-semibold border border-zinc-700 shadow-sm"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                <FileCode className="w-3.5 h-3.5 text-zinc-400" />
                Synthesized AST Patch
              </button>

              <button
                onClick={() => setActiveTab("sandbox")}
                className={`px-3 py-1.5 rounded text-xs transition-all duration-150 flex items-center gap-1.5 ${
                  activeTab === "sandbox"
                    ? "bg-zinc-800 text-zinc-100 font-semibold border border-zinc-700 shadow-sm"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                <Cpu className="w-3.5 h-3.5 text-zinc-400" />
                gVisor Sandbox (0 Egress)
              </button>

              <button
                onClick={() => setActiveTab("crypto")}
                className={`px-3 py-1.5 rounded text-xs transition-all duration-150 flex items-center gap-1.5 ${
                  activeTab === "crypto"
                    ? "bg-zinc-800 text-zinc-100 font-semibold border border-zinc-700 shadow-sm"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                <KeyRound className="w-3.5 h-3.5 text-zinc-400" />
                Ed25519 Cryptographic Proof
              </button>

              <button
                onClick={() => setActiveTab("pr")}
                className={`px-3 py-1.5 rounded text-xs transition-all duration-150 flex items-center gap-1.5 ${
                  activeTab === "pr"
                    ? "bg-zinc-800 text-zinc-100 font-semibold border border-zinc-700 shadow-sm"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                <GitPullRequest className="w-3.5 h-3.5 text-zinc-400" />
                Authorized GitHub PR #42
              </button>
            </div>

            <span className="text-[10px] text-zinc-500 uppercase tracking-wider hidden md:inline">
              Deterministic Gate Inspector
            </span>
          </div>

          {/* Tab 1: AST Patch Diff */}
          {activeTab === "diff" && (
            <div className="space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-zinc-400">
                <div className="flex items-center gap-2">
                  <span className="text-zinc-500">File:</span>
                  <span className="text-zinc-200 font-semibold">app/auth/session.py:42</span>
                  <span className="text-zinc-600">·</span>
                  <span className="text-emerald-400">Tree-sitter Python Grammar: Valid</span>
                </div>
                <button
                  onClick={() =>
                    handleCopy(
                      'cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))',
                      "hero-diff"
                    )
                  }
                  className="px-2 py-0.5 rounded bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-white border border-zinc-800 text-[10px] inline-flex items-center gap-1 transition-colors duration-150"
                >
                  {copiedKey === "hero-diff" ? (
                    <Check className="w-3 h-3 text-emerald-400" />
                  ) : (
                    <Copy className="w-3 h-3" />
                  )}
                  {copiedKey === "hero-diff" ? "Copied" : "Copy Diff"}
                </button>
              </div>

              <div className="p-3.5 bg-zinc-950 rounded border border-zinc-800 overflow-x-auto text-[12px] leading-relaxed">
                <div className="text-zinc-600 select-none text-[11px]">
                  @@ -40,4 +40,4 @@ def authenticate_user(db, user_id: str):
                </div>
                <div className="text-zinc-400">     cursor = db.cursor()</div>
                <div className="bg-rose-950/40 text-rose-300 px-2 py-0.5 rounded -mx-2 flex items-center">
                  <span className="select-none text-rose-500 mr-3 font-bold">-</span>
                  <code>cursor.execute(f&quot;SELECT * FROM users WHERE id = &apos;{`{user_id}`}&apos;&quot;)</code>
                </div>
                <div className="bg-emerald-950/40 text-emerald-300 px-2 py-0.5 rounded -mx-2 flex items-center">
                  <span className="select-none text-emerald-500 mr-3 font-bold">+</span>
                  <code>cursor.execute(&quot;SELECT * FROM users WHERE id = %s&quot;, (user_id,))</code>
                </div>
                <div className="text-zinc-400">     return cursor.fetchone()</div>
              </div>

              <div className="flex flex-wrap items-center justify-between text-[11px] text-zinc-500 pt-1">
                <span>Modification scope: 1 node modified (no arbitrary file rewrite)</span>
                <span className="text-zinc-400">Delta: +1 / -1 lines</span>
              </div>
            </div>
          )}

          {/* Tab 2: gVisor Sandbox Telemetry */}
          {activeTab === "sandbox" && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                <div className="p-3 bg-zinc-900/60 rounded border border-zinc-800 transition-colors duration-150">
                  <div className="text-[10px] text-zinc-500 uppercase">Sandbox Kernel</div>
                  <div className="text-zinc-200 font-semibold mt-0.5">gVisor runsc (user-space)</div>
                  <div className="text-[10px] text-emerald-400 mt-1">✓ Non-root isolated</div>
                </div>

                <div className="p-3 bg-zinc-900/60 rounded border border-zinc-800 transition-colors duration-150">
                  <div className="text-[10px] text-zinc-500 uppercase">Network Egress</div>
                  <div className="text-emerald-400 font-semibold mt-0.5">0 bytes (DROP-ALL)</div>
                  <div className="text-[10px] text-zinc-400 mt-1">iptables deny active</div>
                </div>

                <div className="p-3 bg-zinc-900/60 rounded border border-zinc-800 transition-colors duration-150">
                  <div className="text-[10px] text-zinc-500 uppercase">Test Suite</div>
                  <div className="text-emerald-400 font-semibold mt-0.5">48/48 PASSED</div>
                  <div className="text-[10px] text-zinc-400 mt-1">pytest runtime: 2.8s</div>
                </div>

                <div className="p-3 bg-zinc-900/60 rounded border border-zinc-800 transition-colors duration-150">
                  <div className="text-[10px] text-zinc-500 uppercase">Semgrep Re-scan</div>
                  <div className="text-emerald-400 font-semibold mt-0.5">0 Residual Findings</div>
                  <div className="text-[10px] text-zinc-400 mt-1">CWE-89 eliminated</div>
                </div>
              </div>

              <div className="p-2.5 bg-zinc-950 rounded border border-zinc-800 text-[11px] text-zinc-400 space-y-0.5 font-mono">
                <div>[gVisor] Container initialized with 512MB RAM cap · 0 network interfaces</div>
                <div>[compiler] AST syntax re-parsed cleanly with Tree-sitter Python parser</div>
                <div className="text-emerald-300">
                  [verifier] Regression suite passed with 0 test failures and 0 memory leaks
                  <span className="inline-block w-1.5 h-3 bg-emerald-400 ml-1 animate-terminal-cursor align-middle" />
                </div>
              </div>
            </div>
          )}

          {/* Tab 3: Cryptographic Proof */}
          {activeTab === "crypto" && (
            <div className="space-y-3">
              <div className="space-y-2">
                <div className="p-3 bg-zinc-900/60 rounded border border-zinc-800 transition-colors duration-150">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-zinc-500 uppercase">Canonical SHA-256 Evidence Digest</span>
                    <span className="text-emerald-400 text-[10px] font-bold">VERIFIED</span>
                  </div>
                  <div className="text-emerald-300 font-mono text-[11px] break-all mt-1">
                    0bab05e1ac631d2c9c344c6bcaad7adcaf4decdab15ec2f981c6b32d40eeae28
                  </div>
                </div>

                <div className="p-3 bg-zinc-900/60 rounded border border-zinc-800 transition-colors duration-150">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-zinc-500 uppercase">Ed25519 Signature (RFC 8032)</span>
                    <span className="text-zinc-400 text-[10px]">Key: patchproof-dev-key-1</span>
                  </div>
                  <div className="text-zinc-300 font-mono text-[11px] break-all mt-1">
                    8804f2ef9fbd46d9d642fb5fcdba4c824e10d4363a714e70f3bdfe46ea7f6c888e641c3f1e6e76f2fe257a3f54d2345c2888a4df5794c5a3eaba9f5c12c4d400
                  </div>
                </div>
              </div>

              <div className="flex flex-wrap items-center justify-between text-[11px] text-zinc-400 pt-1">
                <span className="text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Independent offline signature verification supported
                </span>
                <span className="text-zinc-500">Algorithm: Ed25519 (256-bit asymmetric)</span>
              </div>
            </div>
          )}

          {/* Tab 4: Authorized GitHub PR */}
          {activeTab === "pr" && (
            <div className="space-y-3">
              <div className="p-3.5 bg-zinc-950 rounded border border-zinc-800 space-y-2 transition-all duration-150">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="text-xs font-semibold text-zinc-100 font-sans">
                    fix(security): remediate python.sql-injection vulnerability #42
                  </div>
                  <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-[10px] font-bold">
                    PR #42 OPENED
                  </span>
                </div>

                <p className="text-xs text-zinc-400 font-sans leading-relaxed">
                  Synthesized AST patch passed isolated gVisor sandbox testing with 48/48 tests passing and 0 residual findings. Ed25519 cryptographic proof is signed and attached.
                </p>

                <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-zinc-800 text-[11px]">
                  <span className="text-zinc-400">
                    Branch: <strong className="text-zinc-200">patchproof/cwe-89-session</strong>
                  </span>
                  <span className="text-zinc-600">·</span>
                  <span className="text-zinc-400">
                    Target: <strong className="text-zinc-200">main</strong>
                  </span>
                  <span className="text-zinc-600">·</span>
                  <span className="text-emerald-400 font-semibold">✓ 5/5 Verification Gates Passed</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Bottom Control Plane Telemetry Strip */}
        <div className="px-4 sm:px-5 py-2.5 bg-surface-400 border-t border-border-subtle flex flex-wrap items-center justify-between gap-2 text-[11px] text-zinc-400">
          <div className="flex items-center gap-3">
            <span>Runtime: <strong className="text-zinc-200">3.42s</strong></span>
            <span className="text-zinc-600">|</span>
            <span>Egress: <strong className="text-emerald-400">0 Bytes</strong></span>
            <span className="text-zinc-600">|</span>
            <span>Syscalls Filtered: <strong className="text-zinc-200">1,842</strong></span>
          </div>

          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse-subtle" />
            <span className="text-zinc-300">Invariant Satisfied → Write Authorized</span>
          </div>
        </div>
      </div>
    </section>
  );
}
