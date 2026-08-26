import React from "react";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Privacy Policy | PatchProof",
  description: "Privacy policy detailing data retention, repository code handling, and security practices of PatchProof.",
};

export default function PrivacyPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12 space-y-8 font-sans text-xs text-zinc-400">
      <div className="space-y-3 pb-6 border-b border-border-subtle">
        <h1 className="text-3xl font-bold tracking-tight text-zinc-100">Privacy Policy</h1>
        <p className="text-zinc-500 font-mono text-[11px]">Last Updated: August 25, 2026</p>
      </div>

      <div className="space-y-6 leading-relaxed">
        <section className="space-y-2">
          <h2 className="text-base font-semibold text-zinc-200">1. Core Philosophy: Zero Permanent Code Storage</h2>
          <p>
            PatchProof is an automated remediation infrastructure tool. We treat your proprietary source code with the highest security standards. Source code fetched during a remediation job is mounted inside an ephemeral, non-root gVisor container and is permanently destroyed immediately upon completion of the verification run.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-base font-semibold text-zinc-200">2. Information We Ingest</h2>
          <p>
            When you integrate the PatchProof GitHub App, we process:
          </p>
          <ul className="list-disc pl-5 space-y-1">
            <li>GitHub App installation metadata and repository IDs.</li>
            <li>Code scanning alert payloads (e.g. Semgrep or CodeQL vulnerability fingerprints).</li>
            <li>Repository remediation policy definitions (.patchproof.yml).</li>
            <li>Cryptographic evidence records (SHA-256 digests and Ed25519 signatures of verified diffs).</li>
          </ul>
        </section>

        <section className="space-y-2">
          <h2 className="text-base font-semibold text-zinc-200">3. Secrets Redaction & Handling</h2>
          <p>
            PatchProof automatically strips and redacts known secret patterns, private keys, API tokens, and passwords from build logs and execution telemetry before persistence. No customer credentials or private repository keys are exposed in telemetry or database records.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-base font-semibold text-zinc-200">4. Third-Party Disclosures</h2>
          <p>
            We do not sell, rent, or trade your source code, telemetry, or account information with any third parties. Model inference for AST patch generation is executed either locally or through strict zero-data-retention enterprise LLM API endpoints.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-base font-semibold text-zinc-200">5. Contact Information</h2>
          <p>
            For privacy inquiries or data deletion requests, contact security@patchproof.internal.
          </p>
        </section>
      </div>
    </div>
  );
}
