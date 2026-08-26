import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { JobsTable } from "@/components/jobs/JobsTable";
import { JobStatusResponse } from "@/lib/types";

describe("JobsTable", () => {
  const mockJobs: JobStatusResponse[] = [
    {
      job_id: "job-001",
      repository: "octocat/Hello-World",
      commit_sha: "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b",
      event_type: "pull_request",
      target_branch: "main",
      state: "pr_created",
      verified: true,
      pr_number: 99,
      pr_url: "https://github.com/octocat/Hello-World/pull/99",
      is_stale: false,
      created_at: new Date().toISOString(),
      events: [],
    },
    {
      job_id: "job-002",
      repository: "acme/vulnerable-app",
      commit_sha: "4b227777d4dd1fc61c6f884f48641d02b4d121d3",
      event_type: "pull_request",
      state: "failed",
      verified: false,
      error: "Scanner detected syntax error",
      is_stale: false,
      created_at: new Date().toISOString(),
      events: [],
    },
  ];

  it("renders table with status badges and PR links", () => {
    render(<JobsTable jobs={mockJobs} />);

    expect(screen.getByTestId("job-row-job-001")).toBeInTheDocument();
    expect(screen.getByTestId("job-row-job-002")).toBeInTheDocument();
    expect(screen.getByText("octocat/Hello-World")).toBeInTheDocument();
    expect(screen.getByText("acme/vulnerable-app")).toBeInTheDocument();
    expect(screen.getByText("#99")).toBeInTheDocument();
    expect(screen.getByText("PR CREATED")).toBeInTheDocument();
    expect(screen.getByText("FAILED")).toBeInTheDocument();
  });
});
