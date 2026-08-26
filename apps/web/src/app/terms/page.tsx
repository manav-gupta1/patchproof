import React from "react";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Terms of Service | PatchProof",
  description: "Terms of service and usage guidelines for the PatchProof automated security remediation platform.",
};

export default function TermsPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12 space-y-8 font-sans text-xs text-zinc-400">
      <div className="space-y-3 pb-6 border-b border-border-subtle">
        <h1 className="text-3xl font-bold tracking-tight text-zinc-100">Terms of Service</h1>
        <p className="text-zinc-500 font-mono text-[11px]">Last Updated: August 25, 2026</p>
      </div>

      <div className="space-y-6 leading-relaxed">
        <section className="space-y-2">
          <h2 className="text-base font-semibold text-zinc-200">1. Acceptance of Terms</h2>
          <p>
            By accessing or using the PatchProof automated remediation platform, you agree to be bound by these Terms of Service. If you are using PatchProof on behalf of an organization, you represent that you have the authority to bind that organization.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-base font-semibold text-zinc-200">2. Automated Remediation & Human Review</h2>
          <p>
            PatchProof synthesizes automated code proposals and executes deterministic verification gates inside gVisor sandboxes. However, all published pull requests remain subject to your team’s final review and approval. PatchProof never merges pull requests automatically without human authorization.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-base font-semibold text-zinc-200">3. Repository Access & Permissions</h2>
          <p>
            You represent and warrant that you own or have the necessary licenses and permissions to grant PatchProof access to your repositories for scanning, patch synthesis, and sandbox testing.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-base font-semibold text-zinc-200">4. Limitation of Liability</h2>
          <p>
            To the maximum extent permitted by applicable law, PatchProof is provided on an &quot;AS IS&quot; and &quot;AS AVAILABLE&quot; basis without warranties of any kind. PatchProof shall not be liable for any indirect, incidental, special, or consequential damages resulting from code execution or automated pull request generation.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-base font-semibold text-zinc-200">5. Modifications to Service</h2>
          <p>
            We reserve the right to modify or discontinue features of PatchProof at any time. We will provide reasonable advance notice for any breaking changes to API endpoints or webhook specifications.
          </p>
        </section>
      </div>
    </div>
  );
}
