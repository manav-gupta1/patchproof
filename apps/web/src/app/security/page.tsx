import React from "react";
import type { Metadata } from "next";
import Link from "next/link";
import { Shield, Lock, Cpu, Key, FileCheck, CheckCircle2, AlertTriangle, ArrowRight } from "lucide-react";

export const metadata: Metadata = {
  title: "Security & Trust | PatchProof Architecture",
  description: "Learn how PatchProof protects your codebase with gVisor sandboxing, Ed25519 signatures, zero network egress, and fail-closed invariants.",
};

export default function SecurityPage() {
  const permissions = [
    {
      scope: "Repository Metadata",
      access: "Read-only",
      reason: "Inspect repository configuration and webhook routing metadata.",
    },
    {
      scope: "Code Scanning Alerts",
      access: "Read-only",
      reason: "Ingest vulnerability fingerprints from Semgrep, CodeQL, and custom scanners.",
    },
    {
      scope: "Pull Requests",
      access: "Write-only (Verified Only)",
      reason: "Open remediation pull requests on isolated branches ONLY after 5/5 verification gates pass.",
    },
    {
      scope: "Checks / Statuses",
      access: "Write-only",
      reason: "Publish cryptographic verification status check runs to GitHub commits.",
    },
  ];

  const controls = [
    {
      title: "Fail-Closed Execution Invariant",
      icon: <Lock className="w-4 h-4 text-emerald-400" />,
      detail:
        "If any verification check fails (AST parse error, failing test, residual security finding, invalid signature), PatchProof halts execution. Zero writes to GitHub are permitted for unverified patches.",
    },
    {
      title: "gVisor Hardware-Assisted Sandbox Isolation",
      icon: <Cpu className="w-4 h-4 text-emerald-400" />,
      detail:
        "Code execution and verification run inside Google gVisor user-space kernel containers. Untrusted code cannot access host kernel resources or execute privileged syscalls.",
    },
    {
      title: "Zero Network Egress Policy",
      icon: <Shield className="w-4 h-4 text-emerald-400" />,
      detail:
        "Sandboxes enforce strict iptables / network namespace deny-all policies. Synthesized patches cannot make outbound HTTP/TCP calls or exfiltrate environment variables.",
    },
    {
      title: "Secrets Redaction & Ephemeral Workspaces",
      icon: <Key className="w-4 h-4 text-emerald-400" />,
      detail:
        "Environment variables containing API tokens, private keys, or passwords are automatically sanitized and stripped before logging or telemetry persistence. Sandbox workspaces are ephemeral and destroyed after verification.",
    },
    {
      title: "Ed25519 Cryptographic Evidence Bundles",
      icon: <FileCheck className="w-4 h-4 text-emerald-400" />,
      detail:
        "Every published PR includes a canonical SHA-256 JSON digest signed with Ed25519 private keys. Security teams can independently verify the patch authenticity offline.",
    },
    {
      title: "Strict Multi-Tenant Isolation",
      icon: <CheckCircle2 className="w-4 h-4 text-emerald-400" />,
      detail:
        "Repository webhooks and policy models are strictly bound to validated GitHub App installation IDs. Tenants cannot query, inspect, or modify other tenants' jobs or policies.",
    },
  ];

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-12 space-y-16">
      {/* Header */}
      <div className="space-y-4 max-w-3xl">
        <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded bg-zinc-900 border border-zinc-800 text-[11px] font-mono text-zinc-300">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          <span>Security & Trust Model</span>
        </div>
        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-zinc-100 font-sans">
          Security Architecture & Trust Guarantees
        </h1>
        <p className="text-zinc-400 text-sm sm:text-base font-sans leading-relaxed">
          PatchProof was architected from the ground up for zero-trust developer environments. We never compromise code integrity.
        </p>
      </div>

      {/* Core Controls - Linear Specification, No Repetitive Box Grid */}
      <div className="space-y-8 border-t border-border-subtle pt-12">
        <div className="space-y-1">
          <h2 className="text-2xl font-bold tracking-tight text-zinc-100 font-sans">
            6 Active Protection Controls
          </h2>
          <p className="text-zinc-400 text-xs sm:text-sm font-sans">
            Hard architectural enforcement boundaries applied across every remediation job.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-10 gap-y-8 font-mono text-xs">
          {controls.map((ctrl, i) => (
            <div key={i} className="space-y-2 border-l border-zinc-800 pl-4">
              <div className="flex items-center gap-2 font-semibold text-zinc-100 font-sans text-sm">
                {ctrl.icon}
                <span>{ctrl.title}</span>
              </div>
              <p className="text-zinc-400 text-xs sm:text-sm font-sans leading-relaxed">{ctrl.detail}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Threat Model & Mitigations */}
      <div className="space-y-6 border-t border-border-subtle pt-12">
        <div className="max-w-2xl space-y-1">
          <h2 className="text-2xl font-bold tracking-tight text-zinc-100 font-sans">
            Formal Threat Model & Mitigations
          </h2>
          <p className="text-zinc-400 text-xs sm:text-sm font-sans">
            How PatchProof isolates execution against malicious payloads, supply chain attacks, and host escape vectors.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs border-collapse">
            <thead className="border-b border-border-subtle text-zinc-400 text-[10px] uppercase">
              <tr>
                <th className="py-3 px-4 font-medium">Threat Vector</th>
                <th className="py-3 px-4 font-medium">Potential Risk</th>
                <th className="py-3 px-4 font-medium text-emerald-400">PatchProof Mitigation Control</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle text-zinc-300">
              <tr className="hover:bg-zinc-900/30 transition-colors">
                <td className="py-3.5 px-4 font-semibold text-zinc-100">Adversarial SAST Payload</td>
                <td className="py-3.5 px-4 text-zinc-400 font-sans text-xs">Prompt injection via alert rule metadata</td>
                <td className="py-3.5 px-4 text-emerald-300 font-sans text-xs font-medium">Tree-sitter AST validation; LLM outputs constrained to AST node grammar delta</td>
              </tr>
              <tr className="hover:bg-zinc-900/30 transition-colors">
                <td className="py-3.5 px-4 font-semibold text-zinc-100">Outbound Data Exfiltration</td>
                <td className="py-3.5 px-4 text-zinc-400 font-sans text-xs">Synthesized patch calls external C2 server</td>
                <td className="py-3.5 px-4 text-emerald-300 font-sans text-xs font-medium">Kernel-level 0 egress (iptables DROP all outbound TCP/UDP traffic in sandbox)</td>
              </tr>
              <tr className="hover:bg-zinc-900/30 transition-colors">
                <td className="py-3.5 px-4 font-semibold text-zinc-100">Host Kernel Sandbox Escape</td>
                <td className="py-3.5 px-4 text-zinc-400 font-sans text-xs">Privilege escalation via dirty syscalls</td>
                <td className="py-3.5 px-4 text-emerald-300 font-sans text-xs font-medium">Google gVisor user-space kernel (runsc) virtualization; no direct host syscalls</td>
              </tr>
              <tr className="hover:bg-zinc-900/30 transition-colors">
                <td className="py-3.5 px-4 font-semibold text-zinc-100">Secret Token Leakage</td>
                <td className="py-3.5 px-4 text-zinc-400 font-sans text-xs">API keys printed in test execution logs</td>
                <td className="py-3.5 px-4 text-emerald-300 font-sans text-xs font-medium">Automated entropy-based secrets scrubber redacts tokens before DB persistence</td>
              </tr>
              <tr className="hover:bg-zinc-900/30 transition-colors">
                <td className="py-3.5 px-4 font-semibold text-zinc-100">PR Artifact Tampering</td>
                <td className="py-3.5 px-4 text-zinc-400 font-sans text-xs">Attacker intercepts and alters diff</td>
                <td className="py-3.5 px-4 text-emerald-300 font-sans text-xs font-medium">Ed25519 digital signature over canonical SHA-256 evidence payload (RFC 8032)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* GitHub App Scopes */}
      <div className="space-y-6 border-t border-border-subtle pt-12">
        <div className="max-w-2xl space-y-1">
          <h2 className="text-2xl font-bold tracking-tight text-zinc-100 font-sans">
            Minimal GitHub Permissions
          </h2>
          <p className="text-zinc-400 text-xs sm:text-sm font-sans">
            PatchProof adheres to the principle of least privilege. We never request repository administrative access.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs border-collapse">
            <thead className="border-b border-border-subtle text-zinc-400 text-[10px] uppercase">
              <tr>
                <th className="py-3 px-4 font-medium">Scope</th>
                <th className="py-3 px-4 font-medium">Access Level</th>
                <th className="py-3 px-4 font-medium">Purpose</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle text-zinc-300">
              {permissions.map((p, idx) => (
                <tr key={idx} className="hover:bg-zinc-900/30 transition-colors">
                  <td className="py-3.5 px-4 font-semibold text-zinc-100">{p.scope}</td>
                  <td className="py-3.5 px-4">
                    <span className="px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-[11px] text-emerald-400 font-mono">
                      {p.access}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-zinc-400 font-sans text-xs">{p.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* What PatchProof Never Does */}
      <div className="space-y-4 border-t border-border-subtle pt-12 font-mono text-xs">
        <div className="flex items-center gap-2 text-zinc-100 font-semibold text-sm">
          <AlertTriangle className="w-4 h-4 text-amber-400" />
          <span>What PatchProof Never Does</span>
        </div>
        <ul className="space-y-2.5 text-zinc-400 text-xs sm:text-sm font-sans">
          <li className="flex items-start gap-2">
            <span className="text-rose-400 font-bold">✗</span>
            <span>Never pushes directly to your default (<code className="font-mono text-zinc-300">main</code>/<code className="font-mono text-zinc-300">master</code>) branch. All changes are opened as standard pull requests.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-rose-400 font-bold">✗</span>
            <span>Never publishes unverified code. If test suites regress or the vulnerability persists, the job aborts.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-rose-400 font-bold">✗</span>
            <span>Never allows sandbox network access. Sandboxes cannot communicate with external servers.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-rose-400 font-bold">✗</span>
            <span>Never logs or persists secret tokens, passwords, or private key material.</span>
          </li>
        </ul>
      </div>

      {/* CTA */}
      <div className="pt-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-t border-border-subtle text-xs font-mono">
        <span className="text-zinc-400">Need a dedicated VPC deployment or custom signing keys?</span>
        <Link
          href="/contact"
          className="px-5 py-2.5 rounded bg-zinc-100 hover:bg-white text-zinc-950 font-semibold transition-colors inline-flex items-center gap-1.5 self-start sm:self-auto"
        >
          Contact Security Engineering <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
}
