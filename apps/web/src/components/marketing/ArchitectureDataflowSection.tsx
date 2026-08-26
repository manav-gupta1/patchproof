"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  FileCode,
  Cpu,
  ShieldCheck,
  Lock,
  GitPullRequest,
  CheckCircle2,
  KeyRound,
  FileCheck,
  ArrowRight,
  Check,
  ChevronDown,
  Terminal,
} from "lucide-react";

interface ArchitectureNode {
  id: string;
  step: string;
  name: string;
  tag: string;
  summary: string;
  metaKey: string;
  metaValue: string;
  state: "valid" | "isolated" | "verified" | "authorized";
  codeSnippet?: string;
}

export function ArchitectureDataflowSection() {
  const [selectedNode, setSelectedNode] = useState<string>("execution");

  const nodes: ArchitectureNode[] = [
    {
      id: "issue",
      step: "01",
      name: "SECURITY ISSUE",
      tag: "INGESTION",
      summary: "SAST scanner (Semgrep/CodeQL) alerts webhook with exact AST coordinates.",
      metaKey: "Detection",
      metaValue: "CWE-89 · HMAC SHA-256 · app/auth/session.py:42",
      state: "valid",
      codeSnippet: `POST /api/v1/webhooks/github HTTP/1.1\nX-Hub-Signature-256: sha256=4f2a...8c9b\nFinding: python.sql-injection @ line 42`,
    },
    {
      id: "patch",
      step: "02",
      name: "PATCH GENERATION",
      tag: "SYNTHESIS",
      summary: "Tree-sitter isolates vulnerability node and synthesizes targeted syntactic delta.",
      metaKey: "Grammar Scope",
      metaValue: "1 AST Node · Tree-sitter Python · Zero Full-File Rewrite",
      state: "valid",
      codeSnippet: `AST Node: CallExpression[identifier="cursor.execute"]\nDelta: cursor.execute("SELECT ... %s", (user_id,))`,
    },
    {
      id: "execution",
      step: "03",
      name: "ISOLATED EXECUTION",
      tag: "SANDBOX",
      summary: "Code compiles and boots inside non-root gVisor container with zero network egress.",
      metaKey: "Virtualization",
      metaValue: "gVisor runsc (user-space kernel) · 0 Egress (DROP-ALL) · 512MB RAM",
      state: "isolated",
      codeSnippet: `runsc create --bundle=/sandbox/job-8904 --user=1000:1000\niptables -P OUTPUT DROP\nNetwork egress: 0 bytes`,
    },
    {
      id: "verification",
      step: "04",
      name: "VERIFICATION",
      tag: "TEST GATES",
      summary: "Test suites run and security re-scans confirm the vulnerability is eliminated.",
      metaKey: "Gates Passed",
      metaValue: "48/48 Pytest Pass (2.8s) · 0 Residual Findings · Policy OK",
      state: "verified",
      codeSnippet: `pytest tests/ (48 passed in 2.84s)\nsemgrep scan --config=auto (0 findings remaining)`,
    },
    {
      id: "evidence",
      step: "05",
      name: "EVIDENCE",
      tag: "DIGEST",
      summary: "Canonical JSON evidence manifest generated from runtime telemetry and AST diff.",
      metaKey: "Evidence Hash",
      metaValue: "SHA-256: 0bab05e1ac631d2c9c... · Canonical Merkle Bundle",
      state: "verified",
      codeSnippet: `{\n  "sha256_digest": "0bab05e1ac631d2c9c344c6bcaad7adcaf4decdab...",\n  "tests_passed": 48,\n  "egress_bytes": 0\n}`,
    },
    {
      id: "signature",
      step: "06",
      name: "ED25519 SIGNATURE",
      tag: "ATTESTATION",
      summary: "256-bit asymmetric signature seals the evidence bundle for offline verification.",
      metaKey: "Cryptographic Attest",
      metaValue: "RFC 8032 · Key: patchproof-dev-key-1 · Tamper-Evident",
      state: "verified",
      codeSnippet: `Ed25519 Signature (RFC 8032):\n8804f2ef9fbd46d9d642fb5fcdba4c824e10d4363a714e70f3bdfe46ea7f...`,
    },
    {
      id: "write_gate",
      step: "07",
      name: "WRITE GATE",
      tag: "BOUNDARY",
      summary: "Binary fail-closed evaluator verifies proof before granting GitHub write permission.",
      metaKey: "Decision Engine",
      metaValue: "5/5 Gates Valid · Invariant Enforced · Token UNLOCKED",
      state: "authorized",
      codeSnippet: `EVALUATE_WRITE_GATE(job_id="8904"):\nIF all_gates == PASS -> AUTHORIZE_REMOTE_WRITE\nStatus: GRANTED`,
    },
    {
      id: "repository",
      step: "08",
      name: "REPOSITORY",
      tag: "DELIVERY",
      summary: "Signed pull request created with verifiable commit SHA and attached evidence.",
      metaKey: "Dispatch",
      metaValue: "Target: main · PR #42 Opened · Signed Commit Bound",
      state: "authorized",
      codeSnippet: `git push origin patchproof/cwe-89-session\nPOST /repos/octocat/auth-service/pulls #42\nEvidence bundle attached`,
    },
  ];

  const activeNodeData = nodes.find((n) => n.id === selectedNode) || nodes[2];

  return (
    <section className="py-24 max-w-6xl mx-auto px-4 sm:px-6 border-t border-border-muted select-none">
      <div className="space-y-12">
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div className="max-w-xl space-y-2">
            <div className="text-[11px] font-mono uppercase text-emerald-400 tracking-wider font-semibold">
              System Architecture & Dataflow
            </div>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-zinc-100 font-sans">
              How PatchProof Operates
            </h2>
            <p className="text-zinc-400 text-sm font-sans leading-relaxed">
              Every remediation travels through 8 interconnected architectural stages. No speculative writes reach the repository until all gates and cryptographic proofs are satisfied.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs font-mono text-zinc-500 self-start md:self-auto">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse-subtle" />
            <span>Interactive Dataflow Inspector</span>
          </div>
        </div>

        {/* ── 8-STAGE INTERCONNECTED ARCHITECTURE GRID ── */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start font-mono text-xs">
          {/* Left Column: 8 Sequential Stages with Visual Connecting Wire */}
          <div className="lg:col-span-7 space-y-2 relative">
            {/* Continuous Vertical Wire Guide */}
            <div className="absolute left-[23px] top-6 bottom-6 w-px bg-border-subtle z-0 hidden sm:block" />

            {nodes.map((node, index) => {
              const isSelected = selectedNode === node.id;

              return (
                <button
                  key={node.id}
                  onClick={() => setSelectedNode(node.id)}
                  className={`w-full text-left p-3 sm:p-3.5 rounded-md border transition-all duration-150 relative z-10 flex items-start gap-3 group ${
                    isSelected
                      ? "bg-zinc-900 border-zinc-600 shadow-md ring-1 ring-emerald-500/20"
                      : "bg-surface-300 hover:bg-zinc-900/60 border-border-subtle hover:border-border-muted"
                  }`}
                >
                  {/* Step LED Badge */}
                  <div
                    className={`w-7 h-7 rounded border flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5 transition-colors ${
                      isSelected
                        ? "bg-emerald-950 border-emerald-700 text-emerald-300"
                        : "bg-zinc-950 border-border-subtle text-zinc-400 group-hover:text-zinc-200"
                    }`}
                  >
                    {node.step}
                  </div>

                  {/* Stage Summary */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2 mb-0.5">
                      <span
                        className={`font-bold tracking-tight text-xs truncate ${
                          isSelected ? "text-emerald-300" : "text-zinc-200 group-hover:text-zinc-100"
                        }`}
                      >
                        {node.name}
                      </span>
                      <span className="text-[10px] text-zinc-500 uppercase px-1.5 py-0.2 rounded bg-zinc-950 border border-border-subtle shrink-0">
                        {node.tag}
                      </span>
                    </div>

                    <p className="text-[11px] text-zinc-400 font-sans leading-relaxed truncate sm:whitespace-normal">
                      {node.summary}
                    </p>

                    <div className="mt-1.5 pt-1.5 border-t border-border-subtle/60 flex items-center justify-between text-[10px] text-zinc-500">
                      <span className="text-zinc-500">{node.metaKey}:</span>
                      <span className="text-zinc-300 truncate max-w-[280px]">{node.metaValue}</span>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Right Column: Live Stage Inspector & Telemetry Readout */}
          <div className="lg:col-span-5 sticky top-20 space-y-4">
            <div className="rounded-md border border-border-muted bg-surface-300 overflow-hidden shadow-2xl">
              {/* Header */}
              <div className="px-4 py-3 bg-surface-400 border-b border-border-subtle flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  <span className="text-[11px] font-semibold text-zinc-200">
                    STAGE {activeNodeData.step} // {activeNodeData.name}
                  </span>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-bold">
                  {activeNodeData.tag}
                </span>
              </div>

              {/* Inspector Content */}
              <div className="p-4 space-y-3.5">
                <div>
                  <div className="text-[10px] text-zinc-500 uppercase mb-1">Architecture Function:</div>
                  <p className="text-xs text-zinc-200 font-sans leading-relaxed">
                    {activeNodeData.summary}
                  </p>
                </div>

                <div className="p-3 bg-zinc-950 rounded border border-border-subtle space-y-1 text-[11px]">
                  <div className="text-[10px] text-zinc-500 uppercase">Stage Telemetry:</div>
                  <div className="text-emerald-300 font-bold">{activeNodeData.metaKey}</div>
                  <div className="text-zinc-300">{activeNodeData.metaValue}</div>
                </div>

                {activeNodeData.codeSnippet && (
                  <div className="space-y-1">
                    <div className="text-[10px] text-zinc-500 uppercase">Runtime Execution Trace:</div>
                    <pre className="p-3 bg-zinc-950 rounded border border-border-subtle text-zinc-300 overflow-x-auto text-[11px] leading-relaxed">
                      <code>{activeNodeData.codeSnippet}</code>
                    </pre>
                  </div>
                )}
              </div>

              {/* Bottom State Bar */}
              <div className="px-4 py-2.5 bg-surface-400 border-t border-border-subtle flex items-center justify-between text-[11px] text-zinc-400">
                <span>Deterministic Invariant:</span>
                <span className="text-emerald-400 font-semibold flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Verified Gate Passed
                </span>
              </div>
            </div>

            {/* Quick Summary Pill */}
            <div className="p-3 rounded-md bg-zinc-900/60 border border-border-subtle text-[11px] text-zinc-400 flex items-center justify-between">
              <span>Security Invariant:</span>
              <span className="text-zinc-200 font-semibold">Unverified patch → 0 remote writes</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
