import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { LifecycleTimeline } from "@/components/jobs/LifecycleTimeline";
import { FailureBanner } from "@/components/jobs/FailureBanner";
import { JobStatusResponse } from "@/lib/types";

describe("LifecycleTimeline", () => {
  it("renders successful full lifecycle transitions", () => {
    const job: JobStatusResponse = {
      job_id: "job-lifecycle-success",
      repository: "octocat/Hello-World",
      commit_sha: "a".repeat(40),
      event_type: "pull_request",
      state: "pr_created",
      verified: true,
      is_stale: false,
      events: [
        { to_state: "queued", message: "created", created_at: "2026-08-25T10:00:00Z" },
        { to_state: "scanning", message: "scanning", created_at: "2026-08-25T10:00:05Z" },
        { to_state: "analyzing", message: "analyzing", created_at: "2026-08-25T10:00:10Z" },
        { to_state: "patching", message: "patching", created_at: "2026-08-25T10:00:15Z" },
        { to_state: "verifying", message: "verifying", created_at: "2026-08-25T10:00:20Z" },
        { to_state: "verified", message: "verified", created_at: "2026-08-25T10:00:25Z" },
        { to_state: "pr_created", message: "pr_created", created_at: "2026-08-25T10:00:30Z" },
      ],
    };

    render(<LifecycleTimeline job={job} />);

    expect(screen.getByTestId("timeline-step-queued")).toBeInTheDocument();
    expect(screen.getByTestId("timeline-step-scanning")).toBeInTheDocument();
    expect(screen.getByTestId("timeline-step-analyzing")).toBeInTheDocument();
    expect(screen.getByTestId("timeline-step-patching")).toBeInTheDocument();
    expect(screen.getByTestId("timeline-step-verifying")).toBeInTheDocument();
    expect(screen.getByTestId("timeline-step-verified")).toBeInTheDocument();
    expect(screen.getByTestId("timeline-step-pr_created")).toBeInTheDocument();
  });

  it("renders failed state properly with failure marker", () => {
    const job: JobStatusResponse = {
      job_id: "job-lifecycle-failure",
      repository: "octocat/Hello-World",
      commit_sha: "b".repeat(40),
      event_type: "pull_request",
      state: "failed",
      verified: false,
      error: "pytest returned exit code 1",
      is_stale: false,
      events: [
        { to_state: "queued", message: "created" },
        { to_state: "scanning", message: "scanning" },
        { to_state: "analyzing", message: "analyzing" },
        { from_state: "patching", to_state: "failed", message: "Verification failed" },
      ],
    };

    render(<LifecycleTimeline job={job} />);

    expect(screen.getByText(/Failed/)).toBeInTheDocument();
  });
});

describe("FailureBanner", () => {
  it("explains why remediation failed and states no PR was created", () => {
    render(
      <FailureBanner
        error="pytest returned exit code 1"
        state="failed"
      />
    );

    expect(screen.getByTestId("failure-banner")).toBeInTheDocument();
    expect(screen.getByText("Remediation failed")).toBeInTheDocument();
    expect(screen.getByText("Verification did not pass.")).toBeInTheDocument();
    expect(screen.getByText("pytest returned exit code 1")).toBeInTheDocument();
    expect(
      screen.getByText(/PR publication was blocked because verification failed\. No Pull Request was created\./)
    ).toBeInTheDocument();
  });
});
