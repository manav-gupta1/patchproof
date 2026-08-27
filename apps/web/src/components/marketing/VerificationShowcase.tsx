"use client";

import React, { useState } from "react";
import {
  FileCode,
  Cpu,
  KeyRound,
  GitPullRequest,
  Check,
  Copy,
  CheckCircle2,
} from "lucide-react";

type Tab = "diff" | "sandbox" | "crypto" | "pr";

export function VerificationShowcase() {
  const [activeTab, setActiveTab] = useState<Tab>("diff");
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return (
    <section className="py-28 lg:py-44 border-t border-zinc-800/50">
      <div className="max-w-[1600px] mx-auto px-6 sm:px-10 lg:px-16 xl:px-20 space-y-16">

        {/* ── SECTION HEADER ── */}
        <div className="max-w-[900px] space-y-5">
          <p className="text-xs font-mono uppercase tracking-[0.2em] text-zinc-600 font-semibold">
            Verification Evidence
          </p>
          <h2
            className="font-black tracking-tight text-zinc-100 font-sans leading-[0.95]"
            style={{ fontSize: "clamp(2.8rem, 5vw, 5rem)" }}
          >
            What verification actually looks like.
          </h2>
          <p className="text-zinc-500 text-lg font-sans leading-relaxed max-w-[600px]">
            A real CWE-89 SQL injection vulnerability, detected, patched,
            sandbox-verified, and cryptographically sealed.
          </p>
        </div>

        {/* ── VERIFICATION CONSOLE — GALLERY ARTIFACT ── */}
        <div className="rounded-2xl border border-zinc-800/80 bg-zinc-900/30 overflow-hidden font-mono">
          {/* Header bar */}
          <div className="px-8 py-5 bg-zinc-900/60 border-b border-zinc-800/60 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse-subtle" />
              <span className="text-sm font-bold text-zinc-200">
                VERIFICATION RUN #8904
              </span>
              <span className="text-zinc-700">·</span>
              <span className="text-zinc-400 text-sm">
                octocat/auth-service @ 7f9a3b2
              </span>
            </div>
            <span className="px-3 py-1.5 rounded-lg bg-emerald-950/60 border border-emerald-800/40 text-emerald-300 text-xs font-bold tracking-wider">
              5/5 GATES PASSED
            </span>
          </div>

          {/* Tab navigation */}
          <div className="px-8 py-3 bg-zinc-950/40 border-b border-zinc-800/60 flex items-center gap-1 overflow-x-auto">
            {([
              { id: "diff" as Tab, label: "AST Patch", icon: <FileCode className="w-4 h-4" /> },
              { id: "sandbox" as Tab, label: "gVisor Sandbox", icon: <Cpu className="w-4 h-4" /> },
              { id: "crypto" as Tab, label: "Ed25519 Proof", icon: <KeyRound className="w-4 h-4" /> },
              { id: "pr" as Tab, label: "GitHub PR #42", icon: <GitPullRequest className="w-4 h-4" /> },
            ]).map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-150 flex items-center gap-2 whitespace-nowrap ${
                  activeTab === tab.id
                    ? "bg-zinc-800 text-zinc-100 border border-zinc-700"
                    : "text-zinc-500 hover:text-zinc-300"
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="p-8 sm:p-10">
            {/* AST Patch Diff */}
            {activeTab === "diff" && (
              <div className="space-y-6">
                <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-zinc-400">
                  <div className="flex items-center gap-3">
                    <span className="text-zinc-600 text-xs uppercase tracking-wider">File</span>
                    <span className="text-zinc-200 font-semibold">app/auth/session.py:42</span>
                    <span className="text-zinc-700">·</span>
                    <span className="text-rose-400/80 text-xs font-bold uppercase tracking-wider">CWE-89 SQL Injection</span>
                  </div>
                  <button
                    onClick={() => handleCopy('cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))', "diff")}
                    className="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 border border-zinc-700 text-xs inline-flex items-center gap-1.5 transition-colors"
                  >
                    {copiedKey === "diff" ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                    {copiedKey === "diff" ? "Copied" : "Copy"}
                  </button>
                </div>

                <pre
                  className="p-8 bg-zinc-950 rounded-xl border border-zinc-800/60 overflow-x-auto leading-8 font-mono"
                  style={{ fontSize: "15px" }}
                >
                  <div className="text-zinc-700 select-none text-xs pb-3">
                    @@ -40,4 +40,4 @@ def authenticate_user(db, user_id: str):
                  </div>
                  <div className="text-zinc-400">{"    "}cursor = db.cursor()</div>
                  <div className="bg-rose-950/25 text-rose-300 px-4 py-0.5 rounded -mx-4 my-0.5">
                    <span className="select-none text-rose-500 mr-3">-</span>
                    {`cursor.execute(f"SELECT * FROM users WHERE id = '{user_id}'")`}
                  </div>
                  <div className="bg-emerald-950/25 text-emerald-300 px-4 py-0.5 rounded -mx-4 my-0.5">
                    <span className="select-none text-emerald-500 mr-3">+</span>
                    {`cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))`}
                  </div>
                  <div className="text-zinc-400">{"    "}return cursor.fetchone()</div>
                </pre>

                <p className="text-xs text-zinc-600 font-mono">
                  Tree-sitter grammar scope: 1 AST node modified. No arbitrary file rewrite.
                </p>
              </div>
            )}

            {/* gVisor Sandbox */}
            {activeTab === "sandbox" && (
              <div className="space-y-8">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-8">
                  {[
                    { label: "Sandbox", value: "gVisor runsc", status: "Non-root isolated" },
                    { label: "Network", value: "0 bytes egress", status: "iptables DROP-ALL" },
                    { label: "Tests", value: "48/48 passed", status: "pytest 2.8s" },
                    { label: "Re-scan", value: "0 findings", status: "CWE-89 eliminated" },
                  ].map((metric) => (
                    <div key={metric.label} className="space-y-2">
                      <p className="text-xs text-zinc-600 uppercase tracking-wider">{metric.label}</p>
                      <p className="text-emerald-400 font-bold text-base">{metric.value}</p>
                      <p className="text-xs text-zinc-600">{metric.status}</p>
                    </div>
                  ))}
                </div>

                <div
                  className="p-8 bg-zinc-950 rounded-xl border border-zinc-800/60 text-zinc-400 space-y-2 font-mono"
                  style={{ fontSize: "14px", lineHeight: "1.8" }}
                >
                  <div>[gVisor] Container initialized · 512MB RAM · 0 network interfaces</div>
                  <div>[compiler] AST syntax re-parsed with Tree-sitter Python parser</div>
                  <div className="text-emerald-300">
                    [verifier] Regression suite passed: 48/48 tests, 0 failures
                    <span className="inline-block w-2 h-4 bg-emerald-400 ml-1.5 animate-terminal-cursor align-middle" />
                  </div>
                </div>
              </div>
            )}

            {/* Cryptographic Proof */}
            {activeTab === "crypto" && (
              <div className="space-y-8">
                <div className="space-y-6">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-zinc-600 uppercase tracking-wider">SHA-256 Evidence Digest</span>
                      <span className="text-emerald-400 text-xs font-bold tracking-wider">VERIFIED</span>
                    </div>
                    <p className="text-emerald-300 font-mono break-all" style={{ fontSize: "15px" }}>
                      0bab05e1ac631d2c9c344c6bcaad7adcaf4decdab15ec2f981c6b32d40eeae28
                    </p>
                  </div>

                  <div className="border-t border-zinc-800/60 pt-6 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-zinc-600 uppercase tracking-wider">Ed25519 Signature (RFC 8032)</span>
                      <span className="text-xs text-zinc-600">Key: patchproof-dev-key-1</span>
                    </div>
                    <p className="text-zinc-400 font-mono break-all" style={{ fontSize: "15px" }}>
                      8804f2ef9fbd46d9d642fb5fcdba4c824e10d4363a714e70f3bdfe46ea7f6c888e641c3f1e6e76f2fe257a3f54d2345c2888a4df5794c5a3eaba9f5c12c4d400
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2 text-sm text-zinc-500">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>Independent offline verification supported — no network calls required</span>
                </div>
              </div>
            )}

            {/* GitHub PR */}
            {activeTab === "pr" && (
              <div className="space-y-6">
                <div className="space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <h3 className="text-base font-bold text-zinc-100 font-sans">
                      fix(security): remediate python.sql-injection #42
                    </h3>
                    <span className="px-3 py-1.5 rounded-lg bg-emerald-950/60 text-emerald-300 border border-emerald-800/40 text-xs font-bold tracking-wider">
                      PR OPENED
                    </span>
                  </div>
                  <p className="text-sm text-zinc-500 font-sans leading-relaxed">
                    Verified AST patch passed 48/48 tests in gVisor sandbox. Ed25519 proof attached.
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-4 pt-4 border-t border-zinc-800/60 text-sm text-zinc-500">
                  <span>Branch: <strong className="text-zinc-300">patchproof/cwe-89-session</strong></span>
                  <span className="text-zinc-700">·</span>
                  <span>Target: <strong className="text-zinc-300">main</strong></span>
                  <span className="text-zinc-700">·</span>
                  <span className="text-emerald-400 font-bold">✓ 5/5 Gates</span>
                </div>
              </div>
            )}
          </div>

          {/* Footer telemetry */}
          <div className="px-8 py-4 bg-zinc-950/40 border-t border-zinc-800/60 flex flex-wrap items-center justify-between gap-3 text-xs text-zinc-600">
            <div className="flex items-center gap-4 font-mono">
              <span>Runtime: <strong className="text-zinc-400">3.42s</strong></span>
              <span className="text-zinc-700">|</span>
              <span>Egress: <strong className="text-emerald-400">0 bytes</strong></span>
            </div>
            <span className="font-mono">
              patchproof verify --proof evidence.json
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
