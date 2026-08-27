"use client";

import React, { useState } from "react";
import { apiClient } from "@/lib/api";
import { X, Loader2, AlertCircle, CheckCircle2, Shield, Plus } from "lucide-react";

interface ConnectRepositoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConnected?: () => void;
}

export function ConnectRepositoryModal({
  isOpen,
  onClose,
  onConnected,
}: ConnectRepositoryModalProps) {
  const [repository, setRepository] = useState("");
  const [defaultBranch, setDefaultBranch] = useState("main");
  const [minSeverity, setMinSeverity] = useState("medium");
  const [autoRemediate, setAutoRemediate] = useState(true);
  const [autoCreatePr, setAutoCreatePr] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanRepo = repository.trim();
    if (!cleanRepo || !cleanRepo.includes("/") || cleanRepo.split("/").length !== 2) {
      setError("Please provide a valid repository name formatted as 'owner/repo' (e.g. acme/auth-service)");
      return;
    }

    setSaving(true);
    setError(null);
    setSuccess(false);

    try {
      await apiClient.onboardRepository({
        repository: cleanRepo,
        default_branch: defaultBranch.trim() || "main",
        status: "active",
        provider: "github",
        policy: {
          enabled: true,
          minimum_severity: minSeverity,
          auto_remediate: autoRemediate,
          auto_create_pr: autoCreatePr,
          target_branches: [defaultBranch.trim() || "main", "main", "master"],
        },
      });

      setSuccess(true);
      setTimeout(() => {
        if (onConnected) onConnected();
        onClose();
      }, 700);
    } catch (err: any) {
      setError(err.message || "Failed to onboard repository");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
      <div
        className="w-full max-w-lg border border-border-subtle bg-surface-200 rounded-xl shadow-2xl overflow-hidden text-zinc-200"
        role="dialog"
        aria-modal="true"
      >
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-border-subtle flex items-center justify-between bg-surface-300">
          <div className="flex items-center gap-2.5">
            <Shield className="w-4 h-4 text-emerald-400" />
            <span className="font-semibold text-sm text-zinc-100">
              Connect Repository
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-zinc-500 hover:text-zinc-300 hover:bg-surface-100 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {error && (
            <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-800/60 flex items-start gap-2.5 text-xs text-rose-200 font-mono">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-800/60 flex items-center gap-2.5 text-xs text-emerald-300 font-mono">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
              <span>Repository connected and registered successfully!</span>
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-mono uppercase text-zinc-400 tracking-wider mb-1.5">
                GitHub Repository (owner/repo)
              </label>
              <input
                type="text"
                value={repository}
                onChange={(e) => setRepository(e.target.value)}
                placeholder="e.g. acme-corp/payment-service"
                required
                className="w-full px-3.5 py-2 rounded-lg bg-surface-300 border border-border-subtle text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-emerald-500 font-mono"
              />
              <p className="text-[11px] text-zinc-500 mt-1">
                Full GitHub repository identifier monitored for security alerts.
              </p>
            </div>

            <div>
              <label className="block text-xs font-mono uppercase text-zinc-400 tracking-wider mb-1.5">
                Default Branch
              </label>
              <input
                type="text"
                value={defaultBranch}
                onChange={(e) => setDefaultBranch(e.target.value)}
                placeholder="main"
                className="w-full px-3.5 py-2 rounded-lg bg-surface-300 border border-border-subtle text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-emerald-500 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-mono uppercase text-zinc-400 tracking-wider mb-1.5">
                Remediation Policy Threshold
              </label>
              <select
                value={minSeverity}
                onChange={(e) => setMinSeverity(e.target.value)}
                className="w-full px-3.5 py-2 rounded-lg bg-surface-300 border border-border-subtle text-sm text-zinc-100 focus:outline-none focus:border-emerald-500 font-mono"
              >
                <option value="critical">CRITICAL ONLY</option>
                <option value="high">HIGH & CRITICAL</option>
                <option value="medium">MEDIUM, HIGH, & CRITICAL</option>
                <option value="low">LOW & ABOVE</option>
              </select>
            </div>

            <div className="pt-2 space-y-2.5">
              <label className="flex items-center gap-2.5 text-xs text-zinc-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoRemediate}
                  onChange={(e) => setAutoRemediate(e.target.checked)}
                  className="rounded bg-surface-300 border-zinc-700 text-emerald-500 focus:ring-0"
                />
                <span>Automatically synthesize patches in isolated sandbox</span>
              </label>
              <label className="flex items-center gap-2.5 text-xs text-zinc-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoCreatePr}
                  onChange={(e) => setAutoCreatePr(e.target.checked)}
                  className="rounded bg-surface-300 border-zinc-700 text-emerald-500 focus:ring-0"
                />
                <span>Publish Ed25519-signed Pull Request only after verified pass</span>
              </label>
            </div>
          </div>

          <div className="pt-3 border-t border-border-subtle flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-zinc-400 hover:text-zinc-200 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-bold text-xs transition-colors flex items-center gap-1.5 disabled:opacity-50"
            >
              {saving ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Connecting...
                </>
              ) : (
                <>
                  <Plus className="w-3.5 h-3.5" />
                  Connect Repository
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
