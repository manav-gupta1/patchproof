import React from "react";
import { render, screen, waitFor, fireEvent, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import DashboardPage from "@/app/page";
import { apiClient } from "@/lib/api";

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders metric cards, filter pills, and real job metrics", async () => {
    vi.spyOn(apiClient, "getJobs").mockResolvedValue({
      jobs: [
        {
          job_id: "job-1",
          repository: "octocat/Hello-World",
          commit_sha: "abcdef123456",
          event_type: "pull_request",
          state: "pr_created",
          verified: true,
          pr_number: 42,
          pr_url: "https://github.com/octocat/Hello-World/pull/42",
          is_stale: false,
          created_at: new Date().toISOString(),
          events: [],
        },
        {
          job_id: "job-2",
          repository: "acme/api",
          commit_sha: "123456abcdef",
          event_type: "pull_request",
          state: "failed",
          verified: false,
          error: "Verification failed in pytest",
          is_stale: false,
          created_at: new Date().toISOString(),
          events: [],
        },
        {
          job_id: "job-3",
          repository: "acme/web",
          commit_sha: "777777abcdef",
          event_type: "pull_request",
          state: "verifying",
          verified: false,
          is_stale: false,
          created_at: new Date().toISOString(),
          events: [],
        },
      ],
      total: 3,
      limit: 10,
      offset: 0,
    });

    vi.spyOn(apiClient, "getSystemStatus").mockResolvedValue({
      api: "healthy",
      worker: "healthy",
      database: "healthy",
      redis: "healthy",
      sandbox: {
        provider: "gVisor",
        network_policy: "deny",
        isolated: true,
        max_memory_mb: 512,
        cpu_limit: 1.0,
      },
      auth_enabled: true,
      tenant: "Default Tenant",
    });

    vi.spyOn(apiClient, "subscribeToAllEvents").mockImplementation((callbacks) => {
      if (callbacks.onOpen) callbacks.onOpen();
      return () => {};
    });

    render(<DashboardPage />);

    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Protection Overview")).toBeInTheDocument();
      expect(screen.getByTestId("protection-hero")).toBeInTheDocument();
    });

    // Check Metrics
    expect(screen.getByTestId("metric-card-active-remediations")).toHaveTextContent("1");
    expect(screen.getByTestId("metric-card-verified-fixes")).toHaveTextContent("1");
    expect(screen.getByTestId("metric-card-published-prs")).toHaveTextContent("1");
    expect(screen.getByTestId("metric-card-unsafe-writes-blocked")).toHaveTextContent("1");

    // Check Live SSE Badge
    expect(screen.getByTestId("sse-status-live")).toHaveTextContent("Live");

    // Check Filter tabs
    expect(screen.getByTestId("filter-tab-all")).toBeInTheDocument();
    expect(screen.getByTestId("filter-tab-active")).toBeInTheDocument();
    expect(screen.getByTestId("filter-tab-failed")).toBeInTheDocument();

    // Switch filter to "failed"
    fireEvent.click(screen.getByTestId("filter-tab-failed"));
    expect(screen.getByTestId("job-row-job-2")).toBeInTheDocument();
    expect(screen.queryByTestId("job-row-job-1")).not.toBeInTheDocument();
  });

  it("renders empty state when no jobs exist", async () => {
    vi.spyOn(apiClient, "getJobs").mockResolvedValue({
      jobs: [],
      total: 0,
      limit: 10,
      offset: 0,
    });

    vi.spyOn(apiClient, "getSystemStatus").mockResolvedValue({
      api: "healthy",
      worker: "healthy",
      database: "healthy",
      redis: "healthy",
      sandbox: {
        provider: "gVisor",
        network_policy: "deny",
        isolated: true,
        max_memory_mb: 512,
        cpu_limit: 1.0,
      },
      auth_enabled: true,
    });

    vi.spyOn(apiClient, "subscribeToAllEvents").mockReturnValue(() => {});

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByTestId("empty-state")).toBeInTheDocument();
      expect(screen.getByText(/No remediation jobs yet/i)).toBeInTheDocument();
    });
  });

  it("handles real-time SSE job transition and displays notification toast", async () => {
    let capturedCallbacks: any = null;

    vi.spyOn(apiClient, "getJobs").mockResolvedValue({
      jobs: [
        {
          job_id: "job-live-1",
          repository: "acme/service",
          commit_sha: "111111",
          event_type: "pull_request",
          state: "verifying",
          verified: false,
          created_at: new Date().toISOString(),
          events: [],
        },
      ],
      total: 1,
      limit: 10,
      offset: 0,
    });

    vi.spyOn(apiClient, "getSystemStatus").mockResolvedValue({
      api: "healthy",
      worker: "healthy",
      database: "healthy",
      redis: "healthy",
      sandbox: {
        provider: "gVisor",
        network_policy: "deny",
        isolated: true,
        max_memory_mb: 512,
        cpu_limit: 1.0,
      },
      auth_enabled: true,
    });

    vi.spyOn(apiClient, "subscribeToAllEvents").mockImplementation((callbacks) => {
      capturedCallbacks = callbacks;
      if (callbacks.onOpen) callbacks.onOpen();
      return () => {};
    });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByTestId("job-row-job-live-1")).toBeInTheDocument();
    });

    // Simulate incoming verified transition event
    act(() => {
      if (capturedCallbacks?.onTransition) {
        capturedCallbacks.onTransition({
          job_id: "job-live-1",
          repository: "acme/service",
          event_id: 5,
          from_state: "verifying",
          to_state: "verified",
          message: "Verification passed AST inspection",
        });
      }
    });

    // Verify Toast is shown
    await waitFor(() => {
      expect(screen.getByText("✓ Remediation verified")).toBeInTheDocument();
      expect(screen.getByText("acme/service · job-live-1")).toBeInTheDocument();
    });

    // Verify Metric updated
    expect(screen.getByTestId("metric-card-verified-fixes")).toHaveTextContent("1");
  });
});
