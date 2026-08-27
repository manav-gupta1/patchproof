import React from "react";
import type { Metadata } from "next";
import dynamic from "next/dynamic";
import Link from "next/link";
import { ArrowRight, ShieldCheck } from "lucide-react";
import { InteractiveDemo } from "@/components/marketing/InteractiveDemo";

const Pipeline3DPreview = dynamic(
  () =>
    import("@/components/marketing/Pipeline3DPreview").then(
      (mod) => mod.Pipeline3DPreview
    ),
  {
    ssr: false,
    loading: () => (
      <div className="w-full rounded-md border border-border-subtle bg-zinc-950/80 min-h-[220px] flex items-center justify-center font-mono text-xs text-zinc-500">
        <span>Loading 3D Pipeline Transit...</span>
      </div>
    ),
  }
);

export const metadata: Metadata = {
  title: "How It Works | PatchProof Architecture",
  description: "Detailed technical architecture of the PatchProof automated security remediation pipeline.",
};

export default function HowItWorksPage() {
  const steps = [
    {
      num: "01",
      title: "Vulnerability Ingestion & Webhook Verification",
      badge: "HMAC Signed",
      description:
        "PatchProof receives alerts from GitHub Code Scanning (Semgrep, CodeQL, etc.). Every incoming webhook is HMAC-SHA256 signature verified against your secret. The repository is verified against authorized installation records to ensure strict multi-tenant isolation.",
      telemetry: "HMAC-SHA256 signature verified · 5MB payload limit · Path traversal check passed",
    },
    {
      num: "02",
      title: "Repository Remediation Policy Evaluation",
      badge: "Deterministic Policy",
      description:
        "Before generating any code, PatchProof queries the repository policy (.patchproof.yml or DB policy store). It verifies whether the finding meets the minimum severity threshold (e.g., HIGH/CRITICAL), whether auto-remediation is enabled, and whether the target branch is eligible.",
      telemetry: "Policy rule: python.sql-injection · Severity: HIGH · Auto-remediate: ENABLED",
    },
    {
      num: "03",
      title: "AST-Guided Patch Synthesis",
      badge: "Tree-Sitter AST",
      description:
        "Rather than rewriting arbitrary files, PatchProof parses the source code using language-specific Tree-sitter AST grammars. It isolates the vulnerability fingerprint (file, line range, AST node) and synthesizes a minimal, semantic fix preserving existing code formatting.",
      telemetry: "Grammar: Tree-sitter Python · Modified AST nodes: 1 · Synthesized diff lines: +2 / -2",
    },
    {
      num: "04",
      title: "gVisor Zero-Egress Sandbox Execution",
      badge: "gVisor runsc",
      description:
        "The proposed patch is applied strictly inside an isolated workspace within a non-root gVisor container sandbox. Network egress is blocked at the kernel level (0 bytes egress allowed). The workspace runs existing test suites and full security re-scans.",
      telemetry: "Sandbox: gVisor · Network: 0 egress (DENIED) · AST parsed: OK · Tests: 42/42 PASSED",
    },
    {
      num: "05",
      title: "Ed25519 Cryptographic Evidence Generation",
      badge: "SHA-256 + Ed25519",
      description:
        "Upon passing all verification gates, a canonical JSON evidence bundle is assembled containing the verified commit SHA, the AST diff, the pre/post scanner fingerprints, and execution logs. This is hashed with SHA-256 and signed with an Ed25519 private key.",
      telemetry: "Digest: SHA-256 (canonical JSON) · Key: Ed25519 (patchproof-dev-key-1) · Stored: Postgres",
    },
    {
      num: "06",
      title: "Safe Pull Request Publication",
      badge: "Zero Unverified Writes",
      description:
        "The verified patch is published to a dedicated Git branch and an automated Pull Request is opened with the complete cryptographic proof attached. If any prior gate fails, execution halts immediately with zero writes to GitHub.",
      telemetry: "PR: #1 opened · Branch: patchproof/pythonsql-inject · Verified Invariant: ENFORCED",
    },
  ];

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-12 space-y-16">
      {/* Header */}
      <div className="space-y-4 max-w-3xl">
        <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded bg-zinc-900 border border-zinc-800 text-[11px] font-mono text-zinc-300">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          <span>Architecture & Lifecycle</span>
        </div>
        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-zinc-100 font-sans">
          How PatchProof Works
        </h1>
        <p className="text-zinc-400 text-sm sm:text-base font-sans leading-relaxed">
          AI writes the patch. PatchProof verifies it. Every patch must pass isolated gVisor sandbox execution, regression test suites, and Ed25519 cryptographic sealing before any remote write is authorized.
        </p>
      </div>

      {/* 3D Execution Pipeline Visualizer */}
      <div className="space-y-3">
        <div className="text-[11px] font-mono text-emerald-400 uppercase tracking-wider font-semibold">
          Execution Lifecycle Transit
        </div>
        <Pipeline3DPreview />
      </div>

      {/* Architecture Dataflow Spec */}
      <div className="border border-border-subtle rounded-lg bg-surface-300 overflow-hidden font-mono text-xs shadow-xl">
        <div className="px-4 py-2.5 bg-surface-400 border-b border-border-subtle flex items-center justify-between">
          <span className="text-[11px] font-semibold text-zinc-300 uppercase tracking-wider">
            Architecture Dataflow Diagram
          </span>
          <span className="text-[10px] text-zinc-500">RFC-Compliant Pipeline</span>
        </div>
        <pre className="p-4 sm:p-6 bg-zinc-950 text-zinc-300 overflow-x-auto text-[11px] leading-relaxed">
{`┌────────────────────────────────┐
│  GitHub Code Scanning Webhook  │ (Semgrep / CodeQL alert)
└───────────────┬────────────────┘
                │ HMAC-SHA256 Signature Verification + Multi-Tenant Auth
                ▼
┌────────────────────────────────┐
│  Remediation Policy Check      │ (.patchproof.yml / Min Severity Threshold)
└───────────────┬────────────────┘
                │ Policy Allowed (HIGH / CRITICAL)
                ▼
┌────────────────────────────────┐
│  Tree-sitter AST Patch Engine  │ (Grammar-targeted Minimal Semantic Delta)
└───────────────┬────────────────┘
                │ Synthesized Patch Diff
                ▼
┌────────────────────────────────┐
│  gVisor Isolated Sandbox       │ (0 Network Egress · 512MB RAM Cap)
│  ├── 1. Apply AST Patch        │
│  ├── 2. AST Syntax Re-check    │
│  ├── 3. Execute Test Suites    │ (e.g. pytest / npm test)
│  └── 4. Security Re-scan       │ (Confirm finding eliminated)
└───────────────┬────────────────┘
                │ [PASS 5/5 GATES]               │ [FAIL ANY GATE]
                ▼                                ▼
┌────────────────────────────────┐ ┌────────────────────────────────┐
│  Ed25519 Cryptographic Proof   │ │  FAIL-CLOSED ABORT             │
│  (SHA-256 Canonical Evidence)  │ │  (ZERO WRITES TO GITHUB)       │
└───────────────┬────────────────┘ └────────────────────────────────┘
                │ Digital Signature Bound
                ▼
┌────────────────────────────────┐
│  GitHub Pull Request Created   │ (Dedicated branch + Evidence payload)
└────────────────────────────────┘`}
        </pre>
      </div>

      {/* Interactive Workflow Demo */}
      <div className="space-y-4">
        <div className="text-xs font-mono uppercase text-zinc-500">Interactive Pipeline Simulator</div>
        <InteractiveDemo />
      </div>

      {/* Detailed Pipeline Steps - Linear Flow, No Redundant Cards */}
      <div className="space-y-8 border-t border-border-subtle pt-14">
        <div className="space-y-2">
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-zinc-100 font-sans">
            Step-by-Step Verification Pipeline
          </h2>
          <p className="text-zinc-400 text-xs sm:text-sm font-sans">
            Every vulnerability follows a sequential, fail-closed verification path.
          </p>
        </div>

        <div className="space-y-10 divide-y divide-border-subtle/80 font-mono text-xs">
          {steps.map((step, idx) => (
            <div key={step.num} className={`space-y-3 ${idx > 0 ? "pt-10" : "pt-2"}`}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-3">
                  <span className="text-emerald-400 font-bold">{step.num} //</span>
                  <h3 className="text-base font-semibold text-zinc-100 font-sans">{step.title}</h3>
                </div>
                <span className="px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-400 text-[10px]">
                  {step.badge}
                </span>
              </div>

              <p className="text-zinc-400 text-xs sm:text-sm font-sans leading-relaxed">{step.description}</p>

              <div className="p-2.5 bg-zinc-950 rounded border border-zinc-900 text-zinc-500 text-[11px]">
                <code>{`> [telemetry] ${step.telemetry}`}</code>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Fail-Closed Guarantee (Airy Conclusion) */}
      <div className="border-t border-border-subtle pt-14 pb-8 space-y-4 font-mono text-xs">
        <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm">
          <ShieldCheck className="w-5 h-5" />
          <span>The Core Invariant</span>
        </div>
        <p className="text-zinc-300 text-sm font-sans leading-relaxed max-w-2xl">
          PatchProof is strictly <strong>fail-closed</strong>. If at any point the AST syntax check fails, the test suite regresses, the security re-scan detects residual issues, or the signature fails validation, execution halts immediately. No pull requests are created, and zero writes are sent to GitHub.
        </p>
        <div className="pt-2 flex flex-wrap gap-3">
          <Link
            href="/jobs"
            className="px-5 py-2.5 rounded bg-zinc-100 hover:bg-white text-zinc-950 font-semibold transition-colors inline-flex items-center gap-1.5"
          >
            Launch Console <ArrowRight className="w-3.5 h-3.5" />
          </Link>
          <Link
            href="/security"
            className="px-4 py-2.5 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 transition-colors"
          >
            Read Security Guarantees
          </Link>
        </div>
      </div>
    </div>
  );
}
