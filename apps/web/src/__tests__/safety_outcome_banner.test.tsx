import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { SafetyOutcomeBanner } from "@/components/jobs/SafetyOutcomeBanner";
import { JobStatusResponse } from "@/lib/types";

describe("SafetyOutcomeBanner", () => {
  it("renders VERIFIED outcome when job verification passes and evidence is signed", () => {
    const job: JobStatusResponse = {
      job_id: "job-001",
      repository: "octocat/Hello-World",
      commit_sha: "a".repeat(40),
      event_type: "pull_request",
      state: "verified",
      verified: true,
      is_stale: false,
      events: [],
    };

    render(<SafetyOutcomeBanner job={job} />);

    expect(screen.getByTestId("safety-banner-verified")).toBeInTheDocument();
    expect(screen.getByText("VERIFIED → SAFE TO PUBLISH")).toBeInTheDocument();
    expect(
      screen.getByText(/Remediation patch successfully passed syntax AST validation/)
    ).toBeInTheDocument();
  });

  it("renders FAILED outcome with explicit PR publication blocked message", () => {
    const job: JobStatusResponse = {
      job_id: "job-002",
      repository: "acme/legacy-auth",
      commit_sha: "b".repeat(40),
      event_type: "pull_request",
      state: "failed",
      verified: false,
      error: "pytest returned exit code 1 (3 failing tests)",
      is_stale: false,
      events: [],
    };

    render(<SafetyOutcomeBanner job={job} />);

    expect(screen.getByTestId("safety-banner-failed")).toBeInTheDocument();
    expect(screen.getByText("UNVERIFIED → ZERO GITHUB WRITES (PUBLICATION BLOCKED)")).toBeInTheDocument();
    expect(
      screen.getByText(/Patch failed automated sandbox verification\. In accordance with PatchProof safety invariants, GitHub publication was strictly prevented\./)
    ).toBeInTheDocument();
    expect(screen.getByText("pytest returned exit code 1 (3 failing tests)")).toBeInTheDocument();
  });

  it("renders IN PROGRESS outcome during isolated staging", () => {
    const job: JobStatusResponse = {
      job_id: "job-003",
      repository: "acme/api",
      commit_sha: "c".repeat(40),
      event_type: "pull_request",
      state: "verifying",
      verified: null,
      is_stale: false,
      events: [],
    };

    render(<SafetyOutcomeBanner job={job} />);

    expect(screen.getByTestId("safety-banner-inprogress")).toBeInTheDocument();
    expect(screen.getByText("REMEDIATION IN PROGRESS")).toBeInTheDocument();
  });

  it("renders STALE outcome when head commit changes", () => {
    const job: JobStatusResponse = {
      job_id: "job-004",
      repository: "acme/api",
      commit_sha: "d".repeat(40),
      event_type: "pull_request",
      state: "verified",
      verified: true,
      is_stale: true,
      events: [],
    };

    render(<SafetyOutcomeBanner job={job} />);

    expect(screen.getByTestId("safety-banner-stale")).toBeInTheDocument();
    expect(screen.getByText("EVIDENCE STALE — RE-VERIFICATION REQUIRED")).toBeInTheDocument();
  });

  it("renders MERGED outcome when PR was merged into target branch", () => {
    const job: JobStatusResponse = {
      job_id: "job-005",
      repository: "octocat/Hello-World",
      commit_sha: "e".repeat(40),
      event_type: "pull_request",
      state: "pr_merged",
      verified: true,
      merge_commit_sha: "f".repeat(40),
      is_stale: false,
      events: [],
    };

    render(<SafetyOutcomeBanner job={job} />);

    expect(screen.getByTestId("safety-banner-merged")).toBeInTheDocument();
    expect(screen.getByText("PR MERGED INTO TARGET BRANCH")).toBeInTheDocument();
  });
});
