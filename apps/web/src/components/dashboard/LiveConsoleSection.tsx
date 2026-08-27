"use client";

import React, { useEffect, useState, useMemo, useCallback } from "react";
import Link from "next/link";
import { apiClient } from "@/lib/api";
import { JobStatusResponse, SystemStatusResponse, JobTransitionEvent } from "@/lib/types";
import { ProtectionHero } from "@/components/dashboard/ProtectionHero";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { AttentionSection } from "@/components/dashboard/AttentionSection";
import { RecentActivitySection } from "@/components/dashboard/RecentActivitySection";
import { JobsTable } from "@/components/jobs/JobsTable";
import { EmptyState } from "@/components/common/EmptyState";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { SystemStatusWidget } from "@/components/dashboard/SystemStatusWidget";
import { ErrorAlert } from "@/components/common/ErrorAlert";
import { ToastContainer, ToastItem } from "@/components/common/ToastNotification";
import { Cpu, ShieldCheck, GitPullRequest, Lock, RefreshCw, ArrowRight, Play } from "lucide-react";
import { TriggerRemediationModal } from "@/components/repositories/TriggerRemediationModal";
import { useScrollReveal } from "@/hooks/useScrollReveal";

type FilterTab = "all" | "active" | "verified" | "pr_created" | "failed";

export function LiveConsoleSection() {
  const { ref, isRevealed } = useScrollReveal({ threshold: 0.1 });
  const [jobs, setJobs] = useState<JobStatusResponse[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<FilterTab>("all");
  const [sseConnected, setSseConnected] = useState<boolean | null>(null);
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const [isTriggerModalOpen, setIsTriggerModalOpen] = useState(false);
  const seenToastKeys = React.useRef<Set<string>>(new Set());

  const addToast = useCallback((toast: Omit<ToastItem, "id">) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    const newToast: ToastItem = { ...toast, id };
    setToasts((prev) => [...prev.slice(-4), newToast]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, toast.durationMs || 5000);
  }, []);

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [jobsRes, sysRes] = await Promise.all([
        apiClient.getJobs({ limit: 50 }),
        apiClient.getSystemStatus().catch(() => null),
      ]);
      setJobs(jobsRes.jobs || []);
      setSystemStatus(sysRes);
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();

    const unsubscribe = apiClient.subscribeToAllEvents({
      onOpen: () => {
        setSseConnected(true);
      },
      onTransition: (event: JobTransitionEvent) => {
        const toStateLower = (event.to_state || "").toLowerCase();

        setJobs((prevJobs) => {
          const index = prevJobs.findIndex((j) => j.job_id === event.job_id);
          if (index >= 0) {
            const updated = [...prevJobs];
            updated[index] = {
              ...updated[index],
              state: event.to_state,
              pr_number: event.pr_number || updated[index].pr_number,
              pr_url: event.pr_url || updated[index].pr_url,
              verified: ["verified", "pr_created", "pr_updated", "pr_merged"].includes(toStateLower),
            };
            return updated;
          } else {
            const newJob: JobStatusResponse = {
              job_id: event.job_id,
              repository: event.repository,
              commit_sha: "0000000",
              event_type: "pull_request",
              state: event.to_state,
              verified: ["verified", "pr_created", "pr_updated", "pr_merged"].includes(toStateLower),
              pr_number: event.pr_number,
              pr_url: event.pr_url,
              is_stale: false,
              events: [],
              created_at: new Date().toISOString(),
            };
            return [newJob, ...prevJobs];
          }
        });

        // Trigger notification toasts for key terminal states
        const toastKey = `${event.job_id}:${event.to_state}`;
        if (!seenToastKeys.current.has(toastKey)) {
          seenToastKeys.current.add(toastKey);

          if (toStateLower === "verified") {
            addToast({
              type: "success",
              title: "✓ Remediation verified",
              description: `${event.repository} · ${event.job_id}`,
            });
          } else if (toStateLower === "pr_created") {
            addToast({
              type: "info",
              title: "PR Published to GitHub",
              description: `${event.repository} #${event.pr_number || ""}`,
            });
          } else if (toStateLower === "failed") {
            addToast({
              type: "error",
              title: "Verification failed · Zero GitHub writes",
              description: `${event.repository} · ${event.message || event.job_id}`,
            });
          }
        }
      },
      onError: () => {
        setSseConnected(false);
      },
    });

    return () => {
      unsubscribe();
    };
  }, [addToast]);

  const metrics = useMemo(() => {
    const active = jobs.filter((j) =>
      ["queued", "scanning", "analyzing", "patching", "verifying"].includes(
        (j.state || "").toLowerCase()
      )
    ).length;

    const verified = jobs.filter(
      (j) => j.verified || ["verified", "pr_created", "pr_updated", "pr_merged"].includes((j.state || "").toLowerCase())
    ).length;

    const published = jobs.filter((j) =>
      ["pr_created", "pr_updated", "pr_merged"].includes((j.state || "").toLowerCase())
    ).length;

    const unsafeBlocked = jobs.filter((j) =>
      ["failed", "rejected", "blocked"].includes((j.state || "").toLowerCase())
    ).length;

    return { active, verified, published, unsafeBlocked };
  }, [jobs]);

  const filteredJobs = useMemo(() => {
    if (activeFilter === "all") return jobs;
    if (activeFilter === "active") {
      return jobs.filter((j) =>
        ["queued", "scanning", "analyzing", "patching", "verifying"].includes(
          (j.state || "").toLowerCase()
        )
      );
    }
    if (activeFilter === "verified") {
      return jobs.filter(
        (j) => j.verified || ["verified", "pr_created"].includes((j.state || "").toLowerCase())
      );
    }
    if (activeFilter === "pr_created") {
      return jobs.filter((j) =>
        ["pr_created", "pr_updated", "pr_merged"].includes((j.state || "").toLowerCase())
      );
    }
    if (activeFilter === "failed") {
      return jobs.filter((j) =>
        ["failed", "rejected", "blocked"].includes((j.state || "").toLowerCase())
      );
    }
    return jobs;
  }, [jobs, activeFilter]);

  return (
    <div id="console" ref={ref} className="w-full py-16 lg:py-20 overflow-hidden">
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
      <TriggerRemediationModal isOpen={isTriggerModalOpen} onClose={() => setIsTriggerModalOpen(false)} />

      <div className={`max-w-[1600px] mx-auto px-6 sm:px-10 lg:px-16 xl:px-24 space-y-10 font-mono text-xs sm:text-sm transition-all duration-1000 ${isRevealed ? "opacity-100 translate-y-0" : "opacity-0 translate-y-12"}`}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="text-sm font-mono text-emerald-400 uppercase tracking-wider font-bold">
              Live Operations Telemetry
            </div>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black tracking-tight text-zinc-100 font-sans leading-tight">
              Security Remediation Console
            </h2>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={loadDashboardData}
              className="px-3.5 py-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-border-subtle text-zinc-300 hover:text-white text-xs sm:text-sm font-mono inline-flex items-center gap-2 transition-colors focus-visible:ring-1 focus-visible:ring-zinc-400 focus-visible:outline-none"
              title="Refresh live telemetry"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Refresh
            </button>
            <button
              onClick={() => setIsTriggerModalOpen(true)}
              className="px-3.5 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-zinc-950 text-xs sm:text-sm font-sans font-bold transition-colors inline-flex items-center gap-1.5 shadow-sm focus-visible:ring-1 focus-visible:ring-emerald-400 focus-visible:outline-none"
              data-testid="run-remediation-console-btn"
            >
              <Play className="w-3.5 h-3.5 fill-current" /> Run Remediation
            </button>
            <Link
              href="/jobs"
              className="px-4 py-2 rounded-lg bg-zinc-100 hover:bg-white text-zinc-950 text-xs sm:text-sm font-sans font-semibold transition-colors inline-flex items-center gap-1.5 shadow-sm focus-visible:ring-1 focus-visible:ring-zinc-400 focus-visible:outline-none"
            >
              Full Remediations Explorer <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {loading ? (
          <div className="py-16 flex justify-center" aria-live="polite">
            <LoadingSpinner message="Querying live remediation telemetry..." />
          </div>
        ) : error ? (
          <ErrorAlert message={error} onRetry={loadDashboardData} />
        ) : (
          <div className="space-y-6" aria-live="polite">
            {/* Protection Status Header */}
            <ProtectionHero
              jobs={jobs}
              totalRemediated={metrics.verified}
              verifiedCount={metrics.verified}
              activeCount={metrics.active}
              sseConnected={sseConnected}
            />

            {/* Summary Metrics */}
            <div className="border border-border-muted rounded-md bg-surface-300 grid grid-cols-2 md:grid-cols-4 divide-y md:divide-y-0 md:divide-x divide-border-subtle overflow-hidden shadow-lg">
              <MetricCard
                testId="metric-card-active-remediations"
                label="Active Remediations"
                value={metrics.active}
                sublabel="gVisor sandbox active"
                icon={<Cpu className="w-3.5 h-3.5 text-amber-400" />}
              />
              <MetricCard
                testId="metric-card-verified-fixes"
                label="Verified Fixes"
                value={metrics.verified}
                sublabel="Passed 5/5 gates"
                icon={<ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />}
              />
              <MetricCard
                testId="metric-card-published-prs"
                label="Published PRs"
                value={metrics.published}
                sublabel="RFC 8032 signed"
                icon={<GitPullRequest className="w-3.5 h-3.5 text-zinc-300" />}
              />
              <MetricCard
                testId="metric-card-unsafe-writes-blocked"
                label="Unsafe Writes Blocked"
                value={metrics.unsafeBlocked}
                sublabel="Fail-closed enforced"
                icon={<Lock className="w-3.5 h-3.5 text-rose-400" />}
              />
            </div>

            {/* System Status Infrastructure Widget */}
            <SystemStatusWidget status={systemStatus} />

            {/* Attention Section */}
            <AttentionSection jobs={jobs} />

            {/* Recent Protection Activity Event Stream */}
            <RecentActivitySection jobs={jobs} />

            {/* Remediation Jobs Table */}
            <div className="space-y-3 pt-2">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-border-subtle">
                <div>
                  <h3 className="text-sm font-semibold text-zinc-100 font-sans">
                    Remediation Jobs Telemetry
                  </h3>
                  <p className="text-sm text-zinc-400 font-mono">
                    Showing {filteredJobs.length} of {jobs.length} jobs
                  </p>
                </div>

                {/* Filter Tabs */}
                <div className="flex items-center gap-1 font-mono text-sm overflow-x-auto">
                  <button
                    data-testid="filter-tab-all"
                    onClick={() => setActiveFilter("all")}
                    className={`px-2.5 py-1 rounded transition-colors focus-visible:ring-1 focus-visible:ring-zinc-400 focus-visible:outline-none ${
                      activeFilter === "all"
                        ? "bg-zinc-800 text-zinc-100 font-semibold border border-zinc-700"
                        : "text-zinc-400 hover:text-zinc-200"
                    }`}
                  >
                    All ({jobs.length})
                  </button>
                  <button
                    data-testid="filter-tab-active"
                    onClick={() => setActiveFilter("active")}
                    className={`px-2.5 py-1 rounded transition-colors focus-visible:ring-1 focus-visible:ring-zinc-400 focus-visible:outline-none ${
                      activeFilter === "active"
                        ? "bg-zinc-800 text-zinc-100 font-semibold border border-zinc-700"
                        : "text-zinc-400 hover:text-zinc-200"
                    }`}
                  >
                    Active ({metrics.active})
                  </button>
                  <button
                    data-testid="filter-tab-verified"
                    onClick={() => setActiveFilter("verified")}
                    className={`px-2.5 py-1 rounded transition-colors focus-visible:ring-1 focus-visible:ring-zinc-400 focus-visible:outline-none ${
                      activeFilter === "verified"
                        ? "bg-zinc-800 text-zinc-100 font-semibold border border-zinc-700"
                        : "text-zinc-400 hover:text-zinc-200"
                    }`}
                  >
                    Verified ({metrics.verified})
                  </button>
                  <button
                    data-testid="filter-tab-failed"
                    onClick={() => setActiveFilter("failed")}
                    className={`px-2.5 py-1 rounded transition-colors focus-visible:ring-1 focus-visible:ring-zinc-400 focus-visible:outline-none ${
                      activeFilter === "failed"
                        ? "bg-zinc-800 text-zinc-100 font-semibold border border-zinc-700"
                        : "text-zinc-400 hover:text-zinc-200"
                    }`}
                  >
                    Failed/Blocked ({metrics.unsafeBlocked})
                  </button>
                </div>
              </div>

              {filteredJobs.length === 0 ? (
                <EmptyState
                  title="No remediation jobs yet"
                  description={
                    activeFilter === "all"
                      ? "Waiting for GitHub webhook alerts to trigger automatic remediation jobs."
                      : `No jobs match the current '${activeFilter}' filter.`
                  }
                />
              ) : (
                <div className="border border-border-muted rounded-md bg-surface-300 overflow-hidden shadow-xl">
                  <JobsTable jobs={filteredJobs} />
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
