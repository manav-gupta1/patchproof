"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api";
import { RepositorySummary } from "@/lib/types";
import {
  X,
  Loader2,
  AlertCircle,
  Play,
  ShieldCheck,
  Cpu,
  ArrowRight,
  Lock,
} from "lucide-react";

interface TriggerRemediationModalProps {
  isOpen: boolean;
  onClose: () => void;
  repository?: string | null; // Pre-populated repository name
}

export function TriggerRemediationModal({
  isOpen,
  onClose,
  repository,
}: TriggerRemediationModalProps) {
  const router = useRouter();
  const [repositories, setRepositories] = useState<RepositorySummary[]>([]);
  const [selectedRepo, setSelectedRepo] = useState("");
  const [commitSha, setCommitSha] = useState("main");
  const [filePath, setFilePath] = useState("app.py");
  const [ruleId, setRuleId] = useState("python.sql-injection");
  const [severity, setSeverity] = useState("HIGH");
  const [message, setMessage] = useState("SQL injection in query construction");
  const [codeSnippet, setCodeSnippet] = useState(
    'query = f"SELECT * FROM users WHERE username = \'{user_input}\'"'
  );
  const [autoCreatePr, setAutoCreatePr] = useState(true);

  const [loadingRepos, setLoadingRepos] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (repository) {
      setSelectedRepo(repository);
    } else if (isOpen) {
      const loadRepos = async () => {
        setLoadingRepos(true);
        setError(null);
        try {
          const res = await apiClient.getRepositories();
          setRepositories(res.repositories || []);
          if (res.repositories && res.repositories.length > 0) {
            setSelectedRepo(res.repositories[0].repository);
          }
        } catch (err: any) {
          setError(err.message || "Failed to load repositories list");
        } finally {
          setLoadingRepos(false);
        }
      };
      loadRepos();
    }
  }, [repository, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanRepo = selectedRepo.trim();
    if (!cleanRepo) {
      setError("Please select or configure a repository first.");
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const res = await apiClient.triggerRemediation({
        repository: cleanRepo,
        commit_sha: commitSha.trim() || "main",
        file: filePath.trim() || "app.py",
        start_line: 1,
        end_line: 1,
        rule_id: ruleId.trim() || "python.sql-injection",
        severity,
        message: message.trim() || "Security vulnerability detected",
        code_snippet: codeSnippet.trim() || undefined,
        auto_create_pr: autoCreatePr,
      });

      if (res && res.job_id) {
        router.push(`/jobs/${encodeURIComponent(res.job_id)}`);
        onClose();
      } else if (res && res.error) {
        setError(res.error);
      } else {
        setError("Failed to create remediation job");
      }
    } catch (err: any) {
      if (err.status === 400) {
        setError(`Validation Error: ${err.message || "Invalid repository or parameters"}`);
      } else if (err.status === 401 || err.status === 403) {
        setError(`Authorization Error: ${err.message || "You do not have permission to remediate this repository"}`);
      } else if (err.status === 500) {
        setError(`Queue / Server Error: ${err.message || "Failed to enqueue background remediation task"}`);
      } else if (err.message && err.message.toLowerCase().includes("failed to fetch")) {
        setError("Network Error: Could not connect to the PatchProof backend API. Please check your connection.");
      } else {
        setError(err.message || "Failed to trigger remediation");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div
        className="w-full max-w-xl border border-border-subtle bg-surface-200 rounded-xl shadow-2xl overflow-hidden text-zinc-200"
        role="dialog"
        aria-modal="true"
      >
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-border-subtle flex items-center justify-between bg-surface-300">
          <div className="flex items-center gap-2.5">
            <Play className="w-4 h-4 text-emerald-400" />
            <span className="font-bold text-sm text-zinc-100 font-mono tracking-tight">
              Trigger Automated Remediation
            </span>
            <span className="px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-300 text-[10px] font-mono border border-emerald-800">
              Verified Pipeline
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
        <form onSubmit={handleSubmit} className="p-6 space-y-4 max-h-[82vh] overflow-y-auto">
          {error && (
            <div className="p-3.5 rounded-lg bg-rose-950/40 border border-rose-800/80 flex items-start gap-2.5 text-xs text-rose-200 font-mono">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Technical Pipeline Preview & Security Guarantee */}
          <div className="p-3.5 rounded-lg bg-zinc-950 border border-border-subtle/80 space-y-2.5 font-mono text-xs">
            <div className="flex items-center justify-between text-[11px] text-zinc-400 uppercase tracking-wider">
              <span>Remediation Pipeline</span>
              <span className="text-emerald-400 font-bold">● FAIL-CLOSED</span>
            </div>
            <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-zinc-300">
              <span className="px-1.5 py-0.5 rounded bg-zinc-900 border border-zinc-800">AST</span>
              <ArrowRight className="w-3 h-3 text-zinc-600" />
              <span className="px-1.5 py-0.5 rounded bg-zinc-900 border border-zinc-800">SANDBOX</span>
              <ArrowRight className="w-3 h-3 text-zinc-600" />
              <span className="px-1.5 py-0.5 rounded bg-zinc-900 border border-zinc-800">TEST</span>
              <ArrowRight className="w-3 h-3 text-zinc-600" />
              <span className="px-1.5 py-0.5 rounded bg-zinc-900 border border-zinc-800">POLICY</span>
              <ArrowRight className="w-3 h-3 text-zinc-600" />
              <span className="px-1.5 py-0.5 rounded bg-zinc-900 border border-zinc-800">PROOF</span>
              <ArrowRight className="w-3 h-3 text-zinc-600" />
              <span className="px-1.5 py-0.5 rounded bg-emerald-950/80 border border-emerald-800 text-emerald-300 font-semibold">WRITE</span>
            </div>
            <div className="pt-2 border-t border-zinc-900 flex items-start gap-2 text-[11px] text-zinc-400 font-sans leading-relaxed">
              <Lock className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
              <span>
                <strong className="text-zinc-200">Security Guarantee:</strong> Zero remote GitHub writes occur unless the patch passes isolated sandbox verification, zero-regression tests, and cryptographic policy approval.
              </span>
            </div>
          </div>

          <div className="space-y-4">
            {/* Repository Select / Text */}
            <div>
              <label className="block text-xs font-mono uppercase text-zinc-400 tracking-wider mb-1.5">
                Target Repository
              </label>
              {repository ? (
                <div className="w-full px-3.5 py-2 rounded-lg bg-zinc-900 border border-border-subtle text-sm text-zinc-300 font-mono select-none">
                  {repository}
                </div>
              ) : loadingRepos ? (
                <div className="flex items-center gap-2 text-xs text-zinc-500 font-mono">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Loading onboarded repositories...
                </div>
              ) : repositories.length === 0 ? (
                <div className="w-full p-3 rounded-lg bg-zinc-900/60 border border-zinc-800 text-xs text-amber-300/90 font-mono">
                  No active repositories connected. Onboard one first on the repositories tab.
                </div>
              ) : (
                <select
                  value={selectedRepo}
                  onChange={(e) => setSelectedRepo(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-lg bg-surface-300 border border-border-subtle text-sm text-zinc-100 focus:outline-none focus:border-emerald-500 font-mono"
                >
                  {repositories.map((repo) => (
                    <option key={repo.repository} value={repo.repository}>
                      {repo.repository}
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Commit & File */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-mono uppercase text-zinc-400 tracking-wider mb-1.5">
                  Base Commit / Branch
                </label>
                <input
                  type="text"
                  value={commitSha}
                  onChange={(e) => setCommitSha(e.target.value)}
                  required
                  placeholder="main or commit sha"
                  className="w-full px-3.5 py-2 rounded-lg bg-surface-300 border border-border-subtle text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-emerald-500 font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-mono uppercase text-zinc-400 tracking-wider mb-1.5">
                  Target File Path
                </label>
                <input
                  type="text"
                  value={filePath}
                  onChange={(e) => setFilePath(e.target.value)}
                  required
                  placeholder="e.g. app/auth/session.py"
                  className="w-full px-3.5 py-2 rounded-lg bg-surface-300 border border-border-subtle text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-emerald-500 font-mono"
                />
              </div>
            </div>

            {/* Rule & Severity */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-mono uppercase text-zinc-400 tracking-wider mb-1.5">
                  Rule ID
                </label>
                <input
                  type="text"
                  value={ruleId}
                  onChange={(e) => setRuleId(e.target.value)}
                  required
                  placeholder="python.sql-injection"
                  className="w-full px-3.5 py-2 rounded-lg bg-surface-300 border border-border-subtle text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-emerald-500 font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-mono uppercase text-zinc-400 tracking-wider mb-1.5">
                  Severity
                </label>
                <select
                  value={severity}
                  onChange={(e) => setSeverity(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-lg bg-surface-300 border border-border-subtle text-sm text-zinc-100 focus:outline-none focus:border-emerald-500 font-mono"
                >
                  <option value="CRITICAL">CRITICAL</option>
                  <option value="HIGH">HIGH</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="LOW">LOW</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-mono uppercase text-zinc-400 tracking-wider mb-1.5">
                Vulnerability Message
              </label>
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                required
                className="w-full px-3.5 py-2 rounded-lg bg-surface-300 border border-border-subtle text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-emerald-500 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-mono uppercase text-zinc-400 tracking-wider mb-1.5">
                Code Snippet / Context
              </label>
              <textarea
                value={codeSnippet}
                onChange={(e) => setCodeSnippet(e.target.value)}
                rows={3}
                className="w-full px-3.5 py-2 rounded-lg bg-surface-300 border border-border-subtle text-xs text-zinc-100 focus:outline-none focus:border-emerald-500 font-mono"
              />
            </div>

            <div className="pt-1">
              <label className="flex items-center gap-2.5 text-xs text-zinc-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoCreatePr}
                  onChange={(e) => setAutoCreatePr(e.target.checked)}
                  className="rounded bg-surface-300 border-zinc-700 text-emerald-500 focus:ring-0"
                />
                <span>Automatically publish Pull Request if verification passes</span>
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
              data-testid="submit-remediation-button"
              disabled={submitting || (!repository && repositories.length === 0)}
              className="px-5 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-bold text-xs transition-colors flex items-center gap-1.5 disabled:opacity-50 shadow-sm font-mono tracking-tight"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Running Pipeline...
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-current" />
                  Run Remediation
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
