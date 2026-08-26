import React from "react";
import { render, screen, waitFor, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import JobDetailPage from "@/app/jobs/[jobId]/page";
import { apiClient } from "@/lib/api";
import { JobStatusResponse, SseSubscriptionCallbacks } from "@/lib/types";

describe("JobDetailPage SSE Live Integration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("displays SSE Connected indicator and updates timeline in real-time when event arrives", async () => {
    const initialJob: JobStatusResponse = {
      job_id: "job-sse-live-001",
      repository: "octocat/Hello-World",
      commit_sha: "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b",
      event_type: "pull_request",
      state: "scanning",
      verified: null,
      is_stale: false,
      created_at: new Date().toISOString(),
      events: [
        { to_state: "queued", message: "Job created" },
        { to_state: "scanning", message: "Scanning source" },
      ],
    };

    vi.spyOn(apiClient, "getJob").mockResolvedValue(initialJob);
    vi.spyOn(apiClient, "getJobEvidence").mockResolvedValue({
      evidence_id: "ev-001",
      job_id: "job-sse-live-001",
      commit_sha: initialJob.commit_sha,
      repository: initialJob.repository,
      verified: true,
      finding_count: 1,
    });

    let sseCallbacks: SseSubscriptionCallbacks = {};
    vi.spyOn(apiClient, "subscribeToJobEvents").mockImplementation((jobId, callbacks) => {
      sseCallbacks = callbacks;
      if (callbacks.onOpen) callbacks.onOpen();
      return () => {};
    });

    render(<JobDetailPage />);

    await waitFor(() => {
      expect(screen.getByTestId("job-detail-page")).toBeInTheDocument();
      expect(screen.getByTestId("sse-status-indicator")).toHaveTextContent("SSE Connected");
    });

    // Simulate transition event arriving over SSE
    act(() => {
      if (sseCallbacks.onEvent) {
        sseCallbacks.onEvent({
          job_id: "job-sse-live-001",
          event_id: 3,
          from_state: "scanning",
          to_state: "analyzing",
          message: "AST syntax analysis",
          created_at: new Date().toISOString(),
        });
      }
    });

    await waitFor(() => {
      expect(screen.getByTestId("timeline-step-analyzing")).toBeInTheDocument();
    });

    // Simulate terminal event arriving over SSE
    act(() => {
      if (sseCallbacks.onTerminal) {
        sseCallbacks.onTerminal({
          job_id: "job-sse-live-001",
          state: "pr_created",
          error: null,
          pr_number: 42,
          pr_url: "https://github.com/octocat/Hello-World/pull/42",
          is_stale: false,
        });
      }
    });

    await waitFor(() => {
      expect(screen.getByTestId("safety-banner-verified")).toBeInTheDocument();
    });
  });
});
