import React from "react";
import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { FAQAccordion } from "@/components/marketing/FAQAccordion";

export const metadata: Metadata = {
  title: "FAQ | PatchProof Automated Security Remediation",
  description: "Frequently asked questions about PatchProof, AST patch synthesis, gVisor sandboxing, and GitHub permissions.",
};

export default function FAQPage() {
  const securityFAQs = [
    {
      question: "What is PatchProof?",
      answer:
        "PatchProof is a security verification system for AI-generated code patches. When security scanners detect vulnerabilities, AI synthesizes a candidate fix. PatchProof executes the patch inside an isolated gVisor sandbox, verifies test suites and security policies, seals cryptographic evidence, and authorizes the write only after all gates pass.",
    },
    {
      question: "Does PatchProof automatically modify my repository?",
      answer:
        "No. PatchProof never modifies your default branch or pushes commits directly. All verified remediations are delivered as standard GitHub Pull Requests on isolated branches (e.g. patchproof/...) for human code review.",
    },
    {
      question: "What happens when a patch fails verification?",
      answer:
        "Execution immediately halts. PatchProof enforces a strict fail-closed invariant: 'Unverified patch → zero GitHub writes'. If unit tests fail or the vulnerability is not eliminated, no branch is pushed and no PR is opened.",
    },
    {
      question: "How does the gVisor sandbox prevent code escape?",
      answer:
        "Verification runs inside Google's gVisor container runtime (runsc), intercepting application system calls in user space without granting access to the host kernel. Network egress is blocked at the packet layer (0 bytes outbound allowed).",
    },
    {
      question: "What permissions does PatchProof require on GitHub?",
      answer:
        "PatchProof requires Read access to metadata and code scanning alerts, and Write access only to Pull Requests and Checks. PatchProof never requests administrative repository access.",
    },
    {
      question: "Can I define custom repository policies?",
      answer:
        "Yes. You can customize remediation rules using `.patchproof.yml` in your repository or through the web dashboard. You can configure minimum severity thresholds, auto-PR publishing toggles, and target branch filters.",
    },
    {
      question: "Is PatchProof suitable for production repositories?",
      answer:
        "Yes. PatchProof is designed for production codebases with high test coverage. Because every patch must pass your existing test suites and a full security re-scan before delivery, breaking changes are automatically caught and blocked.",
    },
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12 space-y-12">
      {/* Header */}
      <div className="space-y-4 max-w-2xl">
        <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded bg-zinc-900 border border-zinc-800 text-[11px] font-mono text-zinc-300">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          <span>Frequently Asked Questions</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-zinc-100 font-sans">
          Technical Answers & Security FAQ
        </h1>
        <p className="text-zinc-400 text-sm sm:text-base font-sans leading-relaxed">
          Everything you need to know about PatchProof permissions, verification gates, and sandbox isolation.
        </p>
      </div>

      {/* Accordion */}
      <FAQAccordion items={securityFAQs} />

      {/* Still have questions */}
      <div className="p-6 rounded-lg border border-border-subtle bg-surface-300 flex flex-col sm:flex-row sm:items-center justify-between gap-4 font-mono text-xs">
        <div>
          <h3 className="text-sm font-semibold text-zinc-100 font-sans">Have a custom security requirement?</h3>
          <p className="text-zinc-400 text-xs font-sans mt-0.5">
            Our security engineering team is happy to review your VPC or threat model requirements.
          </p>
        </div>
        <Link
          href="/contact"
          className="px-4 py-2 rounded bg-zinc-100 hover:bg-white text-zinc-950 font-semibold transition-colors inline-flex items-center gap-1 shrink-0"
        >
          Contact Engineering <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
}
