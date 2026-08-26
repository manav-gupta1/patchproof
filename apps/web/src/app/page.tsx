import React from "react";
import type { Metadata } from "next";
import Link from "next/link";
import { HeroVerificationControlPlane } from "@/components/marketing/HeroVerificationControlPlane";
import { ZeroUnverifiedWritesSection } from "@/components/marketing/ZeroUnverifiedWritesSection";
import { ArchitectureDataflowSection } from "@/components/marketing/ArchitectureDataflowSection";
import { LiveConsoleSection } from "@/components/dashboard/LiveConsoleSection";
import { InteractiveDemo } from "@/components/marketing/InteractiveDemo";
import { FAQAccordion } from "@/components/marketing/FAQAccordion";
import {
  Shield,
  CheckCircle2,
  Lock,
  ArrowRight,
  FileCode,
  Check,
  AlertTriangle,
  Cpu,
  Fingerprint,
  KeyRound,
  Key,
} from "lucide-react";

export const metadata: Metadata = {
  title: "PatchProof | Automated Security Patching Proven Before GitHub",
  description:
    "PatchProof ingests vulnerability alerts, synthesizes AST patches, verifies them in isolated 0-egress gVisor sandboxes, and publishes Ed25519-signed pull requests. Zero unverified writes to GitHub.",
  openGraph: {
    title: "PatchProof | Automated Security Patching Proven Before GitHub",
    description:
      "Automated security patching with gVisor sandbox verification and Ed25519 cryptographic evidence. Zero unverified writes to GitHub.",
    url: "https://patchproof.dev",
    siteName: "PatchProof",
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "PatchProof | Automated Security Patching Proven Before GitHub",
    description:
      "Automated security patching with gVisor sandbox verification and Ed25519 cryptographic evidence. Zero unverified writes to GitHub.",
    creator: "@patchproof_dev",
  },
};

export default function DashboardPage() {
  const previewFAQs = [
    {
      question: "How does PatchProof guarantee zero unverified writes to GitHub?",
      answer:
        "PatchProof enforces a hard architectural boundary: code patches are synthesized and executed inside an isolated, non-root gVisor sandbox with 0 network egress. The GitHub PR publisher is only invoked if the AST syntax parses cleanly, test suites pass, security re-scans confirm the vulnerability is eliminated, and an Ed25519 cryptographic signature is issued. If any gate fails, execution immediately halts with zero remote writes.",
    },
    {
      question: "What permissions does the PatchProof GitHub App require?",
      answer:
        "PatchProof requires Read access to repository metadata and code scanning alerts, and Write access only to Pull Requests and Checks. PatchProof never requests administrative access, cannot modify protected branch rules, and will never push directly to your default branch.",
    },
    {
      question: "Can we customize remediation policies per repository?",
      answer:
        "Yes. You can define repository-level policies via `.patchproof.yml` or through the Web GUI / REST API. Policies allow you to specify minimum severity thresholds (e.g. only High and Critical), auto-remediation behavior, auto-PR publishing toggles, and target branch filters.",
    },
    {
      question: "How does cryptographic evidence verification work?",
      answer:
        "Every verified remediation produces a canonical JSON payload containing the AST diff, the pre- and post-patch scanner fingerprints, and sandbox execution logs. This payload is hashed with SHA-256 and signed with Ed25519. Security teams can independently verify the signature offline without connecting to PatchProof.",
    },
  ];

  return (
    <div className="space-y-0 text-zinc-200 selection:bg-emerald-950 selection:text-emerald-300">
      {/* ── 1. PRODUCT-DRIVEN SECURITY VERIFICATION HERO ── */}
      <HeroVerificationControlPlane />

      {/* ── 2. ZERO UNVERIFIED WRITES // SYSTEM INVARIANT SECTION ── */}
      <ZeroUnverifiedWritesSection />

      {/* ── 3. SECTION 3 — 8-STAGE ARCHITECTURE DATAFLOW VISUALIZATION ── */}
      <ArchitectureDataflowSection />

      {/* ── 4. SECTION 4 — CRYPTOGRAPHIC ATTESTATION LEDGER ── */}
      <section className="py-24 border-t border-border-muted bg-zinc-950/60">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            {/* Left Column: Cryptographic Chain of Custody */}
            <div className="lg:col-span-5 space-y-6">
              <div className="space-y-3">
                <div className="text-[11px] font-mono uppercase text-emerald-400 tracking-wider font-semibold">
                  Attestation Ledger // RFC 8032
                </div>
                <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-zinc-100 font-sans">
                  Cryptographic evidence establishes trust before write.
                </h2>
                <p className="text-zinc-400 text-sm font-sans leading-relaxed">
                  Rather than asserting safety, PatchProof binds a verifiable cryptographic evidence manifest to every remediation. Security teams can independently verify the Ed25519 signature offline without network access.
                </p>
              </div>

              {/* Three Core Guarantees */}
              <div className="space-y-3 font-mono text-xs">
                <div className="p-3.5 rounded bg-surface-300 border border-border-subtle space-y-1">
                  <div className="flex items-center justify-between text-zinc-200 font-semibold text-[11px]">
                    <span>01. Deterministic SHA-256 Digest</span>
                    <span className="text-emerald-400 text-[10px]">CANONICAL</span>
                  </div>
                  <p className="text-zinc-400 text-xs font-sans leading-relaxed">
                    Hashed across the verified commit SHA, AST diff, and sandbox container test execution logs.
                  </p>
                </div>

                <div className="p-3.5 rounded bg-surface-300 border border-border-subtle space-y-1">
                  <div className="flex items-center justify-between text-zinc-200 font-semibold text-[11px]">
                    <span>02. Asymmetric RFC 8032 Signature</span>
                    <span className="text-emerald-400 text-[10px]">ED25519</span>
                  </div>
                  <p className="text-zinc-400 text-xs font-sans leading-relaxed">
                    Signed with 256-bit asymmetric private keys. Any code alteration invalidates the signature.
                  </p>
                </div>

                <div className="p-3.5 rounded bg-surface-300 border border-border-subtle space-y-1">
                  <div className="flex items-center justify-between text-zinc-200 font-semibold text-[11px]">
                    <span>03. Zero-Trust Offline Verification</span>
                    <span className="text-emerald-400 text-[10px]">STANDALONE</span>
                  </div>
                  <p className="text-zinc-400 text-xs font-sans leading-relaxed">
                    Verify patch authenticity independently using OpenSSL or Python cryptography with no network calls.
                  </p>
                </div>
              </div>
            </div>

            {/* Right Column: Authentic JSON Cryptographic Attestation Block */}
            <div className="lg:col-span-7">
              <div className="rounded-md border border-border-muted bg-surface-300 font-mono text-xs overflow-hidden shadow-2xl">
                <div className="px-4 py-3 bg-surface-400 border-b border-border-subtle flex items-center justify-between">
                  <div className="flex items-center gap-2 text-zinc-200">
                    <KeyRound className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="text-[11px] font-semibold">ATTESTATION CERTIFICATE // RFC 8032</span>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-[10px] font-bold">
                    SIGNATURE: VALID
                  </span>
                </div>

                <div className="p-4 bg-zinc-950/90 text-zinc-300 text-[11px] leading-relaxed overflow-x-auto space-y-1">
                  <div className="text-zinc-500">// Canonical Evidence Bundle Manifest</div>
                  <div>&#123;</div>
                  <div className="pl-4"><span className="text-zinc-500">&quot;schema&quot;</span>: <span className="text-emerald-300">&quot;https://patchproof.dev/schemas/v1/evidence.json&quot;</span>,</div>
                  <div className="pl-4"><span className="text-zinc-500">&quot;run_id&quot;</span>: <span className="text-zinc-300">&quot;8904-sec-cwe89&quot;</span>,</div>
                  <div className="pl-4"><span className="text-zinc-500">&quot;target_repo&quot;</span>: <span className="text-zinc-300">&quot;octocat/auth-service&quot;</span>,</div>
                  <div className="pl-4"><span className="text-zinc-500">&quot;base_commit&quot;</span>: <span className="text-zinc-300">&quot;7f9a3b2c1d4e5f6a&quot;</span>,</div>
                  <div className="pl-4"><span className="text-zinc-500">&quot;isolation&quot;</span>: &#123;</div>
                  <div className="pl-8"><span className="text-zinc-500">&quot;provider&quot;</span>: <span className="text-zinc-300">&quot;gVisor runsc&quot;</span>,</div>
                  <div className="pl-8"><span className="text-zinc-500">&quot;network_egress_bytes&quot;</span>: <span className="text-emerald-300">0</span>,</div>
                  <div className="pl-8"><span className="text-zinc-500">&quot;tests_passed&quot;</span>: <span className="text-emerald-300">42</span>,</div>
                  <div className="pl-8"><span className="text-zinc-500">&quot;residual_findings&quot;</span>: <span className="text-emerald-300">0</span></div>
                  <div className="pl-4">&#125;,</div>
                  <div className="pl-4"><span className="text-zinc-500">&quot;sha256_digest&quot;</span>: <span className="text-emerald-300">&quot;0bab05e1ac631d2c9c344c6bcaad7adcaf4decdab15ec2f981c6b32d40eeae28&quot;</span>,</div>
                  <div className="pl-4"><span className="text-zinc-500">&quot;ed25519_signature&quot;</span>: <span className="text-zinc-300">&quot;8804f2ef9fbd46d9d642fb5fcdba4c824e10d4363a714e70f3bdfe46ea7f6c88...&quot;</span>,</div>
                  <div className="pl-4"><span className="text-zinc-500">&quot;signer_key_id&quot;</span>: <span className="text-zinc-300">&quot;patchproof-dev-key-1&quot;</span></div>
                  <div>&#125;</div>
                </div>

                <div className="px-4 py-2.5 bg-surface-400 border-t border-border-subtle flex flex-wrap items-center justify-between gap-2 text-[11px] text-zinc-400">
                  <span>Offline Verification Command:</span>
                  <code className="text-emerald-300 bg-zinc-900 px-2 py-0.5 rounded border border-zinc-800 text-[10px]">
                    patchproof verify --proof evidence.json
                  </code>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── 5. SECTION 5 — LIVE CONSOLE (Client Component) ── */}
      <LiveConsoleSection />

      {/* ── 6. SECTION 6 — FORMAL SECURITY ISOLATION SPECIFICATION ── */}
      <section className="py-24 border-t border-border-muted bg-surface-400">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 space-y-12">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div className="max-w-2xl space-y-2">
              <div className="text-[11px] font-mono text-emerald-400 uppercase tracking-wider font-semibold">
                Security Architecture Specification
              </div>
              <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-zinc-100 font-sans">
                Deterministic System Isolation
              </h2>
              <p className="text-zinc-400 text-sm font-sans leading-relaxed">
                Deterministic security controls enforced across the kernel, network, syntax, and cryptographic layers.
              </p>
            </div>

            <Link
              href="/security"
              className="text-xs font-mono text-emerald-400 hover:text-emerald-300 inline-flex items-center gap-1 transition-colors self-start md:self-auto"
            >
              Inspect Threat Model & Proofs <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Structured Security Isolation Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 font-mono text-xs">
            <div className="p-4 rounded-md border border-border-subtle bg-surface-300 space-y-2">
              <div className="flex items-center justify-between text-[10px] text-zinc-500">
                <span>01 // EXECUTION LAYER</span>
                <span className="text-emerald-400 font-semibold">ISOLATED</span>
              </div>
              <h3 className="text-sm font-semibold text-zinc-100 font-sans">gVisor User Kernel</h3>
              <p className="text-zinc-400 text-xs font-sans leading-relaxed">
                Non-root user-space kernel (runsc) virtualization. Untrusted code has zero direct host syscall exposure.
              </p>
            </div>

            <div className="p-4 rounded-md border border-border-subtle bg-surface-300 space-y-2">
              <div className="flex items-center justify-between text-[10px] text-zinc-500">
                <span>02 // NETWORK LAYER</span>
                <span className="text-emerald-400 font-semibold">0 EGRESS</span>
              </div>
              <h3 className="text-sm font-semibold text-zinc-100 font-sans">Kernel-Level Drop-All</h3>
              <p className="text-zinc-400 text-xs font-sans leading-relaxed">
                Strict iptables deny-all rules. Outbound TCP/UDP packets are blocked, preventing C2 beaconing and exfiltration.
              </p>
            </div>

            <div className="p-4 rounded-md border border-border-subtle bg-surface-300 space-y-2">
              <div className="flex items-center justify-between text-[10px] text-zinc-500">
                <span>03 // SYNTACTIC LAYER</span>
                <span className="text-emerald-400 font-semibold">CONFINED</span>
              </div>
              <h3 className="text-sm font-semibold text-zinc-100 font-sans">Tree-sitter AST Scoping</h3>
              <p className="text-zinc-400 text-xs font-sans leading-relaxed">
                Grammar graph validation isolates patches strictly to the vulnerable AST node, preventing arbitrary file corruption.
              </p>
            </div>

            <div className="p-4 rounded-md border border-border-subtle bg-surface-300 space-y-2">
              <div className="flex items-center justify-between text-[10px] text-zinc-500">
                <span>04 // TELEMETRY LAYER</span>
                <span className="text-emerald-400 font-semibold">REDACTED</span>
              </div>
              <h3 className="text-sm font-semibold text-zinc-100 font-sans">Secret Scrubbing</h3>
              <p className="text-zinc-400 text-xs font-sans leading-relaxed">
                Entropy-based credential scrubber automatically strips API keys and tokens before database persistence.
              </p>
            </div>

            <div className="p-4 rounded-md border border-border-subtle bg-surface-300 space-y-2 lg:col-span-2">
              <div className="flex items-center justify-between text-[10px] text-zinc-500">
                <span>05 // ATTESTATION LAYER</span>
                <span className="text-emerald-400 font-semibold">RFC 8032</span>
              </div>
              <h3 className="text-sm font-semibold text-zinc-100 font-sans">Ed25519 Cryptographic Proof</h3>
              <p className="text-zinc-400 text-xs font-sans leading-relaxed">
                Binary fail-closed gate: unverified patches never receive a digital signature and zero write operations reach GitHub.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── 7. SECTION 7 — INTERACTIVE VERIFICATION PIPELINE SIMULATOR ── */}
      <section className="py-24 max-w-6xl mx-auto px-4 sm:px-6 border-t border-border-muted">
        <div className="space-y-8">
          <div className="max-w-2xl space-y-2">
            <div className="text-[11px] font-mono uppercase text-emerald-400 tracking-wider font-semibold">
              Live Threat Confrontation Simulator
            </div>
            <h2 className="text-3xl font-bold tracking-tight text-zinc-100 font-sans">
              See the Verification Pipeline in Action
            </h2>
            <p className="text-zinc-400 text-sm font-sans leading-relaxed">
              Experience why PatchProof exists: an unsafe patch that weakens authentication is caught and blocked at the write gate, while a verified fix passes with signed cryptographic proof.
            </p>
          </div>

          <InteractiveDemo />
        </div>
      </section>

      {/* ── 8. SECTION 8 — FREQUENTLY ASKED QUESTIONS ── */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 py-24 border-t border-border-muted">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-start">
          <div className="lg:col-span-4 space-y-3">
            <h2 className="text-2xl font-bold tracking-tight text-zinc-100 font-sans">
              Frequently Asked Questions
            </h2>
            <p className="text-zinc-400 text-xs font-sans leading-relaxed">
              Technical answers regarding sandbox isolation boundaries, zero-egress policies, and Ed25519 evidence verification.
            </p>
            <div className="pt-2">
              <Link
                href="/faq"
                className="text-xs font-mono text-emerald-400 hover:text-emerald-300 transition-colors inline-flex items-center gap-1 focus-visible:ring-1 focus-visible:ring-zinc-400 focus-visible:outline-none"
              >
                View all FAQs <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          <div className="lg:col-span-8">
            <FAQAccordion items={previewFAQs} />
          </div>
        </div>
      </section>

      {/* ── 9. SECTION 9 — FINAL CTA (Single Clear Destination) ── */}
      <section className="border-t border-border-muted bg-surface-400">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-28 sm:py-36 text-center space-y-6">
          <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-zinc-100 font-sans">
            Ready to verify your first patch?
          </h2>
          <p className="text-zinc-400 text-sm sm:text-base font-sans max-w-xl mx-auto leading-relaxed">
            Install the PatchProof GitHub App, configure repository policies, and protect your codebase with fail-closed remediation boundaries.
          </p>
          <div className="pt-4 flex flex-wrap justify-center gap-4 font-mono text-xs">
            <a
              href="#console"
              className="px-6 py-3 rounded bg-zinc-100 hover:bg-white text-zinc-950 font-semibold transition-colors shadow-sm inline-flex items-center gap-1.5 focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none"
            >
              Launch Console <ArrowRight className="w-3.5 h-3.5" />
            </a>
            <Link
              href="/docs"
              className="px-5 py-3 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-200 transition-colors focus-visible:ring-1 focus-visible:ring-zinc-400 focus-visible:outline-none"
            >
              Read Documentation
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
