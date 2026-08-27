"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiClient } from "@/lib/api";
import { RepositorySummary } from "@/lib/types";
import { EmptyState } from "@/components/common/EmptyState";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { ErrorAlert } from "@/components/common/ErrorAlert";
import { RepositoryPolicyModal } from "@/components/repositories/RepositoryPolicyModal";
import { ConnectRepositoryModal } from "@/components/repositories/ConnectRepositoryModal";
import { TriggerRemediationModal } from "@/components/repositories/TriggerRemediationModal";
import { formatRelativeTime } from "@/lib/utils";
import { RefreshCw, ArrowRight, Settings2, Plus, Play } from "lucide-react";

export default function RepositoriesPage() {
  const [repositories, setRepositories] = useState<RepositorySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPolicyRepo, setSelectedPolicyRepo] = useState<string | null>(null);
  const [selectedRemediationRepo, setSelectedRemediationRepo] = useState<string | null>(null);
  const [isConnectModalOpen, setIsConnectModalOpen] = useState(false);

  const loadRepositories = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.getRepositories();
      setRepositories(res.repositories || []);
    } catch (err: any) {
      setError(err.message || "Failed to load repositories");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRepositories();
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto" data-testid="repositories-page">
      {/* Connect Repository Modal */}
      <ConnectRepositoryModal
        isOpen={isConnectModalOpen}
        onClose={() => setIsConnectModalOpen(false)}
        onConnected={loadRepositories}
      />

      {/* Policy Modal */}
      {selectedPolicyRepo && (
        <RepositoryPolicyModal
          repository={selectedPolicyRepo}
          isOpen={Boolean(selectedPolicyRepo)}
          onClose={() => setSelectedPolicyRepo(null)}
          onSaved={loadRepositories}
        />
      )}

      {/* Trigger Remediation Modal */}
      {selectedRemediationRepo && (
        <TriggerRemediationModal
          repository={selectedRemediationRepo}
          isOpen={Boolean(selectedRemediationRepo)}
          onClose={() => setSelectedRemediationRepo(null)}
        />
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-4 border-b border-border-subtle pb-4">
        <div>
          <div className="text-[11px] font-mono uppercase tracking-wider text-zinc-500">
            PROTECT / INVENTORY
          </div>
          <h1 className="text-lg sm:text-xl font-semibold text-zinc-100 font-sans tracking-tight mt-0.5">
            Protected Repositories
          </h1>
          <p className="text-xs text-zinc-400 mt-0.5">
            Monitored code repositories with active remediation boundaries and automated security policies
          </p>
        </div>
        <div className="flex items-center gap-3 self-start sm:self-auto">
          <button
            onClick={() => setIsConnectModalOpen(true)}
            id="connect-repository-btn"
            className="px-3.5 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-zinc-950 text-xs font-bold transition-colors inline-flex items-center gap-1.5 shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            Connect Repository
          </button>
          <button
            onClick={loadRepositories}
            disabled={loading}
            className="text-xs font-mono text-zinc-400 hover:text-zinc-200 inline-flex items-center gap-1.5 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3 h-3 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {error && <ErrorAlert message={error} onRetry={loadRepositories} />}

      {/* Repository Inventory */}
      {loading ? (
        <LoadingSpinner label="Loading protected repositories..." />
      ) : repositories.length === 0 ? (
        <div className="border border-border-subtle rounded-lg p-8 bg-surface-300">
          <EmptyState
            title="No repositories connected"
            description="Install the PatchProof GitHub App or trigger a webhook alert to begin protecting repositories."
          />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {repositories.map((repo) => (
            <div
              key={repo.repository}
              className="border border-border-subtle bg-surface-300 rounded-lg p-4 sm:p-5 flex flex-col justify-between space-y-3.5 hover:border-zinc-700 transition-colors"
              data-testid={`repo-card-${repo.repository.replace(/\//g, "-")}`}
            >
              {/* Top: Repo name and Status */}
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="text-sm font-semibold font-mono text-zinc-100">
                    {repo.repository}
                  </div>
                  <div className="flex items-center gap-2 mt-1 text-xs">
                    <span className="inline-flex items-center gap-1.5 font-mono text-[11px] text-emerald-400">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      Protected · {repo.installation_status}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setSelectedRemediationRepo(repo.repository)}
                    className="px-2.5 py-1 bg-emerald-950/80 hover:bg-emerald-900/90 text-emerald-400 hover:text-emerald-300 border border-emerald-800/80 rounded text-xs font-mono inline-flex items-center gap-1.5 transition-colors"
                    data-testid={`remediate-${repo.repository}`}
                  >
                    <Play className="w-3 h-3 text-emerald-400 fill-current" />
                    Remediate
                  </button>
                  <button
                    onClick={() => setSelectedPolicyRepo(repo.repository)}
                    className="px-2.5 py-1 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 border border-zinc-800 rounded text-xs font-mono inline-flex items-center gap-1.5 transition-colors"
                    data-testid={`edit-policy-${repo.repository}`}
                  >
                    <Settings2 className="w-3 h-3 text-zinc-400" />
                    Policy
                  </button>
                </div>
              </div>

              {/* Counts Strip */}
              <div className="grid grid-cols-3 gap-2 py-2 border-y border-border-subtle font-mono text-xs">
                <div>
                  <div className="text-[10px] text-zinc-500 uppercase">Total jobs</div>
                  <div className="text-zinc-200 font-semibold mt-0.5">{repo.total_jobs}</div>
                </div>
                <div>
                  <div className="text-[10px] text-zinc-500 uppercase">Active</div>
                  <div className={`font-semibold mt-0.5 ${repo.active_jobs > 0 ? "text-indigo-400" : "text-zinc-500"}`}>
                    {repo.active_jobs}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-zinc-500 uppercase">Verified PRs</div>
                  <div className="text-emerald-400 font-semibold mt-0.5">{repo.verified_prs}</div>
                </div>
              </div>

              {/* Policy summary & View Link */}
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-[11px] text-zinc-500">
                  Last activity: {formatRelativeTime(repo.last_activity)}
                </span>

                <Link
                  href={`/jobs?repository=${encodeURIComponent(repo.repository)}`}
                  className="text-xs font-mono text-zinc-400 hover:text-zinc-100 transition-colors inline-flex items-center gap-1"
                >
                  Remediations <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
