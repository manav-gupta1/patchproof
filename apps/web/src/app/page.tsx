import React from "react";
import type { Metadata } from "next";
import Link from "next/link";
import { HeroSection } from "@/components/marketing/HeroVerificationControlPlane";
import { ZeroUnverifiedWritesSection } from "@/components/marketing/ZeroUnverifiedWritesSection";
import { ArchitectureDataflowSection } from "@/components/marketing/ArchitectureDataflowSection";
import { VerificationShowcase } from "@/components/marketing/VerificationShowcase";
import { LiveConsoleSection } from "@/components/dashboard/LiveConsoleSection";
import { FAQAccordion } from "@/components/marketing/FAQAccordion";
import { ArrowRight, KeyRound } from "lucide-react";

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
        'Yes. You can define repository-level policies via `.patchproof.yml` or through the Web GUI / REST API. Policies allow you to specify minimum severity thresholds (e.g. only High and Critical), auto-remediation behavior, auto-PR publishing toggles, and target branch filters.',
    },
    {
      question: "How does cryptographic evidence verification work?",
      answer:
        "Every verified remediation produces a canonical JSON payload containing the AST diff, the pre- and post-patch scanner fingerprints, and sandbox execution logs. This payload is hashed with SHA-256 and signed with Ed25519. Security teams can independently verify the signature offline without connecting to PatchProof.",
    },
  ];

  return (
    <div className="text-zinc-200 selection:bg-emerald-950 selection:text-emerald-300">
      {/* ── 1. HERO — headline + 3D chamber, ~90vh ── */}
      <HeroSection />

      {/* ── 2. PROBLEM — editorial comparison ── */}
      <ZeroUnverifiedWritesSection />

      {/* ── 3. HOW IT WORKS — 4 stages ── */}
      <ArchitectureDataflowSection />

      {/* ── 4. VERIFICATION SHOWCASE — tabbed evidence ── */}
      <VerificationShowcase />

      {/* ── 5. CRYPTOGRAPHIC ATTESTATION ── */}
      <section className="py-28 lg:py-44 border-t border-zinc-800/50">
        <div className="max-w-[1400px] mx-auto px-6 sm:px-10 lg:px-16 xl:px-20">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-16 lg:gap-28 items-start">

            {/* Left Column — bare numbered list, no card chrome */}
            <div className="lg:col-span-5 space-y-12">
              <div className="space-y-5">
                <p className="text-xs font-mono uppercase tracking-[0.2em] text-zinc-600 font-semibold">
                  Cryptographic Attestation
                </p>
                <h2
                  className="font-black tracking-tight text-zinc-100 font-sans leading-[0.95]"
                  style={{ fontSize: "clamp(2.4rem, 4vw, 4rem)" }}
                >
                  Evidence before
                  <br />
                  the write.
                </h2>
                <p className="text-zinc-500 text-base sm:text-lg font-sans leading-relaxed">
                  PatchProof binds a verifiable evidence manifest to every
                  remediation. Security teams verify the Ed25519 signature
                  offline with no network access required.
                </p>
              </div>

              {/* Three guarantees — bare numbered list, no card borders */}
              <div className="space-y-8 font-mono">
                {[
                  {
                    n: "01",
                    title: "SHA-256 Digest",
                    tag: "CANONICAL",
                    desc: "Hashed across commit SHA, AST diff, and sandbox execution logs.",
                  },
                  {
                    n: "02",
                    title: "Ed25519 Signature",
                    tag: "RFC 8032",
                    desc: "256-bit asymmetric signing. Any code alteration invalidates the proof.",
                  },
                  {
                    n: "03",
                    title: "Offline Verification",
                    tag: "STANDALONE",
                    desc: "Verify with OpenSSL or Python cryptography. No network calls.",
                  },
                ].map((item) => (
                  <div key={item.n} className="flex items-start gap-6">
                    <span className="text-zinc-700 font-bold text-xs mt-1 tabular-nums shrink-0 w-5">
                      {item.n}
                    </span>
                    <div className="space-y-1 min-w-0">
                      <div className="flex items-center gap-3">
                        <span className="text-zinc-200 font-semibold text-sm">{item.title}</span>
                        <span className="text-emerald-500 text-xs font-bold">{item.tag}</span>
                      </div>
                      <p className="text-zinc-600 text-sm font-sans leading-relaxed">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right Column — JSON Attestation Block (actual technical artifact — card appropriate) */}
            <div className="lg:col-span-7">
              <div className="rounded-xl border border-zinc-800/70 bg-zinc-900/30 font-mono overflow-hidden">
                <div className="px-7 py-5 bg-zinc-900/50 border-b border-zinc-800/60 flex items-center justify-between">
                  <div className="flex items-center gap-2.5 text-zinc-200">
                    <KeyRound className="w-4 h-4 text-emerald-400" />
                    <span className="text-sm font-bold">ATTESTATION CERTIFICATE</span>
                  </div>
                  <span className="px-2.5 py-1 rounded-lg bg-emerald-950/50 text-emerald-300 border border-emerald-800/40 text-xs font-bold tracking-wider">
                    SIGNATURE: VALID
                  </span>
                </div>

                <div
                  className="p-7 bg-zinc-950/70 text-zinc-300 leading-8 overflow-x-auto space-y-0.5"
                  style={{ fontSize: "15px" }}
                >
                  <div className="text-zinc-700">// Canonical Evidence Bundle</div>
                  <div>&#123;</div>
                  <div className="pl-6"><span className="text-zinc-500">&quot;schema&quot;</span>: <span className="text-emerald-300">&quot;https://patchproof.dev/schemas/v1/evidence.json&quot;</span>,</div>
                  <div className="pl-6"><span className="text-zinc-500">&quot;run_id&quot;</span>: <span className="text-zinc-300">&quot;8904-sec-cwe89&quot;</span>,</div>
                  <div className="pl-6"><span className="text-zinc-500">&quot;target_repo&quot;</span>: <span className="text-zinc-300">&quot;octocat/auth-service&quot;</span>,</div>
                  <div className="pl-6"><span className="text-zinc-500">&quot;isolation&quot;</span>: &#123;</div>
                  <div className="pl-12"><span className="text-zinc-500">&quot;provider&quot;</span>: <span className="text-zinc-300">&quot;gVisor runsc&quot;</span>,</div>
                  <div className="pl-12"><span className="text-zinc-500">&quot;network_egress_bytes&quot;</span>: <span className="text-emerald-300">0</span>,</div>
                  <div className="pl-12"><span className="text-zinc-500">&quot;tests_passed&quot;</span>: <span className="text-emerald-300">42</span>,</div>
                  <div className="pl-12"><span className="text-zinc-500">&quot;residual_findings&quot;</span>: <span className="text-emerald-300">0</span></div>
                  <div className="pl-6">&#125;,</div>
                  <div className="pl-6"><span className="text-zinc-500">&quot;sha256_digest&quot;</span>: <span className="text-emerald-300">&quot;0bab05e1...40eeae28&quot;</span>,</div>
                  <div className="pl-6"><span className="text-zinc-500">&quot;ed25519_signature&quot;</span>: <span className="text-zinc-400">&quot;8804f2ef...4d400&quot;</span></div>
                  <div>&#125;</div>
                </div>

                <div className="px-7 py-4 bg-zinc-900/50 border-t border-zinc-800/60 flex flex-wrap items-center justify-between gap-3 text-sm text-zinc-600">
                  <span>Offline Verification:</span>
                  <code className="text-emerald-300 bg-zinc-950 px-3 py-1.5 rounded-lg border border-zinc-800/60 text-xs font-mono">
                    patchproof verify --proof evidence.json
                  </code>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── 6. LIVE CONSOLE ── */}
      <LiveConsoleSection />

      {/* ── 7. FAQ ── */}
      <section className="py-28 lg:py-40 border-t border-zinc-800/50">
        <div className="max-w-[1000px] mx-auto px-6 sm:px-10 lg:px-16">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-16 items-start">
            <div className="lg:col-span-4 space-y-5">
              <h2
                className="font-black tracking-tight text-zinc-100 font-sans leading-[0.95]"
                style={{ fontSize: "clamp(2rem, 3.5vw, 3rem)" }}
              >
                Frequently Asked Questions
              </h2>
              <p className="text-zinc-600 text-sm font-sans leading-relaxed">
                Technical answers about sandbox isolation, zero-egress policies,
                and cryptographic evidence verification.
              </p>
              <div className="pt-2">
                <Link
                  href="/faq"
                  className="text-sm font-sans text-zinc-500 hover:text-zinc-300 transition-colors inline-flex items-center gap-2 font-medium"
                >
                  View all FAQs <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>

            <div className="lg:col-span-8">
              <FAQAccordion items={previewFAQs} />
            </div>
          </div>
        </div>
      </section>

      {/* ── 8. FINAL CTA ── */}
      <section className="border-t border-zinc-800/50">
        <div className="max-w-4xl mx-auto px-6 sm:px-10 lg:px-16 py-48 lg:py-64 text-center space-y-10">
          <h2
            className="font-black tracking-tight text-zinc-100 font-sans leading-[0.95]"
            style={{ fontSize: "clamp(3rem, 6vw, 6rem)" }}
          >
            Ready to verify
            <br />
            your first patch?
          </h2>
          <p className="text-zinc-500 text-base sm:text-xl font-sans max-w-2xl mx-auto leading-relaxed">
            Install the PatchProof GitHub App. Configure repository policies.
            Protect your codebase with fail-closed verification.
          </p>
          <div className="pt-4 flex flex-wrap justify-center gap-5 font-sans text-base">
            <a
              href="#console"
              id="final-cta-launch-console"
              className="px-9 py-4 rounded-lg bg-zinc-100 hover:bg-white text-zinc-950 font-bold transition-all shadow-lg hover:shadow-xl inline-flex items-center gap-2.5 focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none"
            >
              Launch Console <ArrowRight className="w-4 h-4" />
            </a>
            <Link
              href="/docs"
              className="px-7 py-4 rounded-lg bg-zinc-900/60 hover:bg-zinc-800/60 border border-zinc-800 text-zinc-400 hover:text-zinc-200 font-medium transition-colors focus-visible:ring-1 focus-visible:ring-zinc-400 focus-visible:outline-none"
            >
              Read Documentation
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
