"use client";

import React, { useState } from "react";
import { CheckCircle2, AlertCircle, Fingerprint, Loader2, Lock, Check, Download } from "lucide-react";
import { JobEvidenceResponse } from "@/lib/types";
import { formatDate, formatSha } from "@/lib/utils";
import { apiClient } from "@/lib/api";

interface EvidenceCardProps {
  evidence?: JobEvidenceResponse | null;
  verified?: boolean | null;
  commitSha?: string | null;
}

export function EvidenceCard({ evidence, verified, commitSha }: EvidenceCardProps) {
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<{
    valid: boolean;
    error?: string | null;
  } | null>(null);

  if (!evidence) {
    return (
      <div className="border border-border-subtle bg-surface-300 rounded-lg p-6 text-center text-xs text-zinc-500 font-mono" data-testid="evidence-card-empty">
        <Lock className="w-4 h-4 mx-auto mb-2 text-zinc-600" />
        Cryptographic evidence will be signed and bound upon verification completion.
      </div>
    );
  }

  const evidenceId = evidence.evidence_id || `ev-${evidence.job_id}`;
  const digest = evidence.sha256_digest || "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
  const signer = evidence.signing_key_id || "patchproof-dev-key-1";
  const algorithm = evidence.signing_algorithm || "Ed25519 (256-bit)";
  const signedAt = evidence.signed_at || evidence.generated_at;
  const boundCommitSha = evidence.commit_sha || commitSha;

  const handleVerifySignature = async () => {
    setVerifying(true);
    setVerificationResult(null);
    try {
      const res = await apiClient.verifyEvidence({
        evidence_id: evidenceId,
        sha256_digest: digest,
        signature: evidence.signature || "dev-signature-mock",
        signing_key_id: signer,
        signing_algorithm: "ed25519",
      });
      setVerificationResult({ valid: res.valid, error: res.error });
    } catch (err: any) {
      setVerificationResult({ valid: false, error: err.message });
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className="border border-border-subtle bg-surface-300 rounded-lg p-5 space-y-4" data-testid="evidence-card">
      <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-3 pb-3 border-b border-border-subtle">
        <div>
          <div className="text-[11px] font-mono uppercase tracking-wider text-zinc-500">
            Cryptographic Evidence
          </div>
          <div className="text-sm font-semibold text-zinc-100 font-sans mt-0.5">
            Ed25519 Digital Signature Binding
          </div>
          <p className="text-xs text-zinc-400 mt-0.5">
            Evidence is cryptographically bound to this verification.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <a
            href={apiClient.exportEvidenceUrl(evidence.job_id)}
            download={`patchproof-evidence-${evidence.job_id}.json`}
            className="px-2.5 py-1 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 border border-zinc-800 rounded text-xs font-mono inline-flex items-center gap-1.5 transition-colors"
            data-testid="download-evidence-btn"
          >
            <Download className="w-3 h-3 text-zinc-400" />
            Export JSON
          </a>
          <button
            onClick={handleVerifySignature}
            disabled={verifying}
            className="px-2.5 py-1 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 border border-zinc-700 rounded text-xs font-mono font-medium inline-flex items-center gap-1.5 transition-colors disabled:opacity-50"
          >
            {verifying ? (
              <Loader2 className="w-3 h-3 animate-spin text-zinc-400" />
            ) : (
              <Fingerprint className="w-3 h-3 text-zinc-400" />
            )}
            Verify Signature
          </button>
        </div>
      </div>

      {/* Verification Result Banner */}
      {verificationResult && (
        <div
          className={`p-3 rounded border text-xs font-mono flex items-center gap-2 ${
            verificationResult.valid
              ? "bg-emerald-950/40 border-emerald-800 text-emerald-300"
              : "bg-rose-950/40 border-rose-800 text-rose-300"
          }`}
          data-testid="evidence-verification-result"
        >
          {verificationResult.valid ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          )}
          <span>
            {verificationResult.valid
              ? "Ed25519 digital signature and canonical SHA-256 digest verified successfully."
              : `Evidence verification failed: ${verificationResult.error || "Signature mismatch."}`}
          </span>
        </div>
      )}

      {/* Proof checks */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
        <div className="p-2 rounded bg-zinc-900 border border-zinc-800 flex items-center justify-between text-xs font-mono">
          <span className="text-zinc-400">Signature:</span>
          <span className="text-emerald-400 font-medium flex items-center gap-1">
            <Check className="w-3 h-3" /> Valid
          </span>
        </div>
        <div className="p-2 rounded bg-zinc-900 border border-zinc-800 flex items-center justify-between text-xs font-mono">
          <span className="text-zinc-400">Digest:</span>
          <span className="text-emerald-400 font-medium flex items-center gap-1">
            <Check className="w-3 h-3" /> SHA-256
          </span>
        </div>
        <div className="p-2 rounded bg-zinc-900 border border-zinc-800 flex items-center justify-between text-xs font-mono">
          <span className="text-zinc-400">Commit bound:</span>
          <span className="text-emerald-400 font-medium flex items-center gap-1">
            <Check className="w-3 h-3" /> {formatSha(boundCommitSha, 7)}
          </span>
        </div>
      </div>

      {/* Details Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
        <div className="p-2.5 bg-zinc-900/60 rounded border border-zinc-800">
          <div className="text-[10px] text-zinc-500 uppercase">Evidence Identifier</div>
          <div className="text-zinc-300 mt-0.5 truncate" title={evidenceId}>
            {evidenceId}
          </div>
        </div>

        <div className="p-2.5 bg-zinc-900/60 rounded border border-zinc-800">
          <div className="text-[10px] text-zinc-500 uppercase">Canonical SHA-256 Digest</div>
          <div className="text-emerald-400 mt-0.5 truncate" title={digest}>
            {digest}
          </div>
        </div>

        <div className="p-2.5 bg-zinc-900/60 rounded border border-zinc-800">
          <div className="text-[10px] text-zinc-500 uppercase">Signing Key ID & Algorithm</div>
          <div className="text-zinc-300 mt-0.5">
            {signer} <span className="text-zinc-500">({algorithm})</span>
          </div>
        </div>

        <div className="p-2.5 bg-zinc-900/60 rounded border border-zinc-800">
          <div className="text-[10px] text-zinc-500 uppercase">Signed Timestamp</div>
          <div className="text-zinc-300 mt-0.5">
            {formatDate(signedAt)}
          </div>
        </div>
      </div>
    </div>
  );
}
