import React from "react";
import type { Metadata } from "next";
import Link from "next/link";
import { BookOpen, Terminal, Shield, Code, Cpu, ArrowRight, ExternalLink, Copy } from "lucide-react";

export const metadata: Metadata = {
  title: "Documentation | PatchProof Automated Security Remediation",
  description: "Developer guides, GitHub App setup, repository policy (.patchproof.yml) configuration, and REST API documentation.",
};

export default function DocsPage() {
  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-12 space-y-16">
      {/* Header */}
      <div className="space-y-4 max-w-3xl">
        <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded bg-zinc-900 border border-zinc-800 text-[11px] font-mono text-zinc-300">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          <span>Documentation & Integration Guides</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-zinc-100 font-sans">
          PatchProof Developer Documentation
        </h1>
        <p className="text-zinc-400 text-sm sm:text-base font-sans leading-relaxed">
          Learn how to install the GitHub App, configure repository remediation policies, query the REST API, and verify Ed25519 cryptographic proofs.
        </p>
      </div>

      {/* Quickstart Guide */}
      <div className="space-y-6 border-t border-border-subtle pt-10">
        <div className="flex items-center gap-2 font-semibold text-zinc-100 font-sans text-xl">
          <Terminal className="w-5 h-5 text-emerald-400" />
          <h2>Quickstart Integration</h2>
        </div>

        <div className="space-y-4 font-mono text-xs">
          <div className="p-4 rounded-lg border border-border-subtle bg-surface-300 space-y-2">
            <div className="text-zinc-300 font-semibold">Step 1: Install PatchProof GitHub App</div>
            <p className="text-zinc-400 font-sans text-xs">
              Install the GitHub App to grant read access to code scanning alerts and write access to pull requests.
            </p>
          </div>

          <div className="p-4 rounded-lg border border-border-subtle bg-surface-300 space-y-2">
            <div className="text-zinc-300 font-semibold">Step 2: Add .patchproof.yml Configuration</div>
            <p className="text-zinc-400 font-sans text-xs">
              Place a configuration file in your repository root to declare remediation rules:
            </p>
            <pre className="p-3 bg-zinc-950 rounded border border-zinc-800 text-zinc-300 overflow-x-auto">
              <code>{`# .patchproof.yml
version: "1.0"
min_severity: "high"
auto_remediate: true
auto_create_pr: true
target_branches:
  - main
  - release/*
sandbox:
  provider: "gvisor"
  timeout_seconds: 300
  network_policy: "deny"`}</code>
            </pre>
          </div>

          <div className="p-4 rounded-lg border border-border-subtle bg-surface-300 space-y-2">
            <div className="text-zinc-300 font-semibold">Step 3: Trigger Remediations</div>
            <p className="text-zinc-400 font-sans text-xs">
              Whenever a code scanning alert fires, PatchProof will automatically ingest the finding, synthesize an AST patch in gVisor, and deliver a verified pull request.
            </p>
          </div>
        </div>
      </div>

      {/* REST API Reference */}
      <div className="space-y-6 border-t border-border-subtle pt-10 font-mono text-xs">
        <div className="flex items-center gap-2 font-semibold text-zinc-100 font-sans text-xl">
          <Code className="w-5 h-5 text-emerald-400" />
          <h2>REST API Reference</h2>
        </div>

        <p className="text-zinc-400 font-sans text-xs">
          All API requests accept <code className="text-zinc-200 bg-zinc-900 px-1.5 py-0.5 rounded border border-zinc-800">Authorization: Bearer &lt;TOKEN&gt;</code> or <code className="text-zinc-200 bg-zinc-900 px-1.5 py-0.5 rounded border border-zinc-800">X-API-Key: &lt;KEY&gt;</code>.
        </p>

        <div className="border border-border-subtle rounded-lg bg-surface-300 overflow-hidden divide-y divide-border-subtle">
          <div className="p-4 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-[10px] font-bold">
                  GET
                </span>
                <span className="font-semibold text-zinc-100">/jobs</span>
              </div>
              <span className="text-[11px] text-zinc-500">Query parameter: ?limit=50&amp;state=verified</span>
            </div>
            <p className="text-zinc-400 font-sans text-xs">List remediation jobs with filtering by state and repository.</p>
            <pre className="p-2.5 bg-zinc-950 rounded border border-zinc-800 text-zinc-300 text-[11px] overflow-x-auto">
              <code>curl -H &quot;Authorization: Bearer $TOKEN&quot; https://api.patchproof.dev/jobs?limit=10</code>
            </pre>
          </div>

          <div className="p-4 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-[10px] font-bold">
                  GET
                </span>
                <span className="font-semibold text-zinc-100">/jobs/{`{job_id}`}</span>
              </div>
              <span className="text-[11px] text-zinc-500">Path parameter: job_id (e.g. job-deliv-alert-2)</span>
            </div>
            <p className="text-zinc-400 font-sans text-xs">Retrieve complete job details, timeline events, and PR metadata.</p>
            <pre className="p-2.5 bg-zinc-950 rounded border border-zinc-800 text-zinc-300 text-[11px] overflow-x-auto">
              <code>curl -H &quot;Authorization: Bearer $TOKEN&quot; https://api.patchproof.dev/jobs/job-deliv-alert-2</code>
            </pre>
          </div>

          <div className="p-4 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-[10px] font-bold">
                  GET
                </span>
                <span className="font-semibold text-zinc-100">/jobs/{`{job_id}`}/evidence</span>
              </div>
              <span className="text-[11px] text-zinc-500">Returns: Canonical JSON Evidence Bundle</span>
            </div>
            <p className="text-zinc-400 font-sans text-xs">Export canonical JSON cryptographic proof with SHA-256 digest and Ed25519 signature.</p>
            <pre className="p-2.5 bg-zinc-950 rounded border border-zinc-800 text-zinc-300 text-[11px] overflow-x-auto">
              <code>curl -H &quot;Authorization: Bearer $TOKEN&quot; https://api.patchproof.dev/jobs/job-deliv-alert-2/evidence &gt; evidence.json</code>
            </pre>
          </div>

          <div className="p-4 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-[10px] font-bold">
                  GET / PUT
                </span>
                <span className="font-semibold text-zinc-100">/repositories/{`{owner}`}/{`{repo}`}/policy</span>
              </div>
              <span className="text-[11px] text-zinc-500">Payload: RepositoryRemediationPolicy</span>
            </div>
            <p className="text-zinc-400 font-sans text-xs">Inspect or update repository remediation policies dynamically.</p>
          </div>

          <div className="p-4 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-[10px] font-bold">
                  GET
                </span>
                <span className="font-semibold text-zinc-100">/events</span>
              </div>
              <span className="text-[11px] text-zinc-500">Protocol: text/event-stream</span>
            </div>
            <p className="text-zinc-400 font-sans text-xs">Server-Sent Events (SSE) stream for real-time lifecycle transitions.</p>
          </div>
        </div>
      </div>

      {/* Offline Evidence Verification */}
      <div className="space-y-4 border-t border-border-subtle pt-10 font-mono text-xs">
        <div className="flex items-center gap-2 font-semibold text-zinc-100 font-sans text-xl">
          <Shield className="w-5 h-5 text-emerald-400" />
          <h2>Offline Evidence Verification</h2>
        </div>
        <p className="text-zinc-400 font-sans text-xs">
          You can independently verify any PatchProof evidence signature using Python cryptography or standard OpenSSL 3 CLI:
        </p>
        <div className="space-y-3">
          <div>
            <div className="text-[11px] text-zinc-400 mb-1">Option A: Python Cryptography (RFC 8032)</div>
            <pre className="p-3 bg-zinc-950 rounded border border-zinc-800 text-zinc-300 overflow-x-auto text-[11px]">
              <code>{`# Verify Ed25519 evidence signature with Python cryptography
from cryptography.hazmat.primitives.asymmetric import ed25519
import json

evidence = json.load(open("evidence.json"))
raw_digest = bytes.fromhex(evidence["sha256_digest"])
signature = bytes.fromhex(evidence["signature"])
public_key = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUBLIC_KEY_HEX))

# Raises InvalidSignature if tampered
public_key.verify(signature, raw_digest)
print("✓ Cryptographic evidence verified successfully")`}</code>
            </pre>
          </div>

          <div>
            <div className="text-[11px] text-zinc-400 mb-1">Option B: OpenSSL 3.0 CLI</div>
            <pre className="p-3 bg-zinc-950 rounded border border-zinc-800 text-zinc-300 overflow-x-auto text-[11px]">
              <code>{`# Extract digest & signature bytes, then verify against public key
openssl pkeyutl -verify -pubin -inkey patchproof_public.pem \\
  -rawin -in digest.bin -sigfile signature.bin`}</code>
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
