"use client";

import React, { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";
import { X, Loader2, AlertCircle, CheckCircle2, Save } from "lucide-react";

interface RepositoryPolicyModalProps {
  repository: string;
  isOpen: boolean;
  onClose: () => void;
  onSaved?: () => void;
}

export function RepositoryPolicyModal({
  repository,
  isOpen,
  onClose,
  onSaved,
}: RepositoryPolicyModalProps) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const [enabled, setEnabled] = useState(true);
  const [minSeverity, setMinSeverity] = useState("medium");
  const [autoRemediate, setAutoRemediate] = useState(true);
  const [autoCreatePr, setAutoCreatePr] = useState(true);
  const [targetBranches, setTargetBranches] = useState("main, master");

  useEffect(() => {
    if (!isOpen || !repository) return;

    const [owner, repo] = repository.split("/");
    if (!owner || !repo) return;

    setLoading(true);
    setError(null);
    setSuccess(false);

    apiClient
      .getRepositoryPolicy(owner, repo)
      .then((policy) => {
        setEnabled(policy.enabled !== false);
        setMinSeverity(policy.minimum_severity || "medium");
        setAutoRemediate(policy.auto_remediate !== false);
        setAutoCreatePr(policy.auto_create_pr !== false);
        const branches = Array.isArray(policy.target_branches)
          ? policy.target_branches.join(", ")
          : "main, master";
        setTargetBranches(branches);
      })
      .catch((err: any) => {
        setError(err.message || "Failed to load policy");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [isOpen, repository]);

  if (!isOpen) return null;

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    const [owner, repo] = repository.split("/");
    if (!owner || !repo) return;

    setSaving(true);
    setError(null);
    setSuccess(false);

    const branchesList = targetBranches
      .split(",")
      .map((b) => b.trim())
      .filter(Boolean);

    try {
      await apiClient.updateRepositoryPolicy(owner, repo, {
        enabled,
        minimum_severity: minSeverity,
        auto_remediate: autoRemediate,
        auto_create_pr: autoCreatePr,
        target_branches: branchesList.length > 0 ? branchesList : ["main"],
      });
      setSuccess(true);
      if (onSaved) onSaved();
      setTimeout(() => {
        onClose();
      }, 1000);
    } catch (err: any) {
      setError(err.message || "Failed to update policy");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-xs"
      data-testid="repository-policy-modal"
    >
      <div className="relative w-full max-w-lg bg-surface-300 rounded-lg border border-border-subtle shadow-xl overflow-hidden font-sans">
        {/* Header */}
        <div className="flex items-center justify-between p-4 sm:p-5 border-b border-border-subtle bg-surface-400">
          <div>
            <div className="text-[10px] font-mono uppercase tracking-wider text-zinc-500">
              Policy Configuration
            </div>
            <h2 className="text-sm font-semibold text-zinc-100 font-mono mt-0.5">
              {repository}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-zinc-400 hover:text-white rounded hover:bg-zinc-800 transition-colors"
            aria-label="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        {loading ? (
          <div className="p-10 flex flex-col items-center justify-center gap-2">
            <Loader2 className="w-5 h-5 animate-spin text-zinc-400" />
            <span className="text-xs font-mono text-zinc-500">Loading policy rules...</span>
          </div>
        ) : (
          <form onSubmit={handleSave} className="p-4 sm:p-5 space-y-3.5">
            {error && (
              <div className="p-2.5 bg-rose-950/40 border border-rose-800 rounded text-xs text-rose-300 flex items-center gap-2 font-mono">
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {success && (
              <div className="p-2.5 bg-emerald-950/40 border border-emerald-800 rounded text-xs text-emerald-300 flex items-center gap-2 font-mono">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Policy configuration updated successfully.</span>
              </div>
            )}

            {/* Enable Policy Toggle */}
            <div className="flex items-center justify-between p-3 rounded bg-zinc-900/60 border border-border-subtle">
              <div>
                <label className="text-xs font-medium text-zinc-200 block">Automated Remediation</label>
                <span className="text-[11px] text-zinc-400 block">
                  Enable autonomous AST synthesis for this repository
                </span>
              </div>
              <input
                type="checkbox"
                checked={enabled}
                onChange={(e) => setEnabled(e.target.checked)}
                className="w-4 h-4 rounded bg-zinc-800 border-zinc-700 accent-emerald-500 focus:ring-emerald-500"
                data-testid="policy-enabled-toggle"
              />
            </div>

            {/* Minimum Severity */}
            <div>
              <label className="text-[11px] font-mono uppercase text-zinc-400 block mb-1">
                Minimum Severity Threshold
              </label>
              <select
                value={minSeverity}
                onChange={(e) => setMinSeverity(e.target.value)}
                className="w-full px-3 py-1.5 bg-zinc-900 border border-zinc-800 rounded text-xs font-mono text-zinc-200 focus:outline-none focus-visible:border-zinc-600"
                data-testid="policy-severity-select"
              >
                <option value="critical">Critical (Highest priority only)</option>
                <option value="high">High (High and Critical)</option>
                <option value="medium">Medium (Medium, High, and Critical)</option>
                <option value="low">Low (All severities)</option>
                <option value="info">Info (Audit mode - all findings)</option>
              </select>
            </div>

            {/* Auto Remediate & Auto PR */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <div className="flex items-center justify-between p-2.5 rounded bg-zinc-900/60 border border-border-subtle">
                <div>
                  <label className="text-xs font-medium text-zinc-200 block">Auto Remediate</label>
                  <span className="text-[10px] text-zinc-400 block">Propose patch diff</span>
                </div>
                <input
                  type="checkbox"
                  checked={autoRemediate}
                  onChange={(e) => setAutoRemediate(e.target.checked)}
                  className="w-4 h-4 rounded bg-zinc-800 border-zinc-700 accent-emerald-500 focus:ring-emerald-500"
                  data-testid="policy-auto-remediate-toggle"
                />
              </div>

              <div className="flex items-center justify-between p-2.5 rounded bg-zinc-900/60 border border-border-subtle">
                <div>
                  <label className="text-xs font-medium text-zinc-200 block">Auto Create PR</label>
                  <span className="text-[10px] text-zinc-400 block">Publish verified PR</span>
                </div>
                <input
                  type="checkbox"
                  checked={autoCreatePr}
                  onChange={(e) => setAutoCreatePr(e.target.checked)}
                  className="w-4 h-4 rounded bg-zinc-800 border-zinc-700 accent-emerald-500 focus:ring-emerald-500"
                  data-testid="policy-auto-create-pr-toggle"
                />
              </div>
            </div>

            {/* Target Branches */}
            <div>
              <label className="text-[11px] font-mono uppercase text-zinc-400 block mb-1">
                Target Branches (comma-separated)
              </label>
              <input
                type="text"
                value={targetBranches}
                onChange={(e) => setTargetBranches(e.target.value)}
                placeholder="main, master, release/*"
                className="w-full px-3 py-1.5 bg-zinc-900 border border-zinc-800 rounded text-xs font-mono text-zinc-200 placeholder-zinc-600 focus:outline-none focus-visible:border-zinc-600"
                data-testid="policy-branches-input"
              />
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end gap-2 pt-3 border-t border-border-subtle">
              <button
                type="button"
                onClick={onClose}
                className="px-3 py-1.5 bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 text-xs font-mono rounded border border-zinc-800 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saving}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-mono font-semibold rounded transition-colors disabled:opacity-50"
                data-testid="save-policy-btn"
              >
                {saving ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-zinc-900" />
                ) : (
                  <Save className="w-3.5 h-3.5 text-zinc-900" />
                )}
                {saving ? "Saving Policy..." : "Save Policy"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
