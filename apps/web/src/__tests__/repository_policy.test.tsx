import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { RepositoryPolicyModal } from "@/components/repositories/RepositoryPolicyModal";
import RepositoriesPage from "@/app/repositories/page";
import { apiClient } from "@/lib/api";

vi.mock("@/lib/api", () => {
  return {
    apiClient: {
      getRepositories: vi.fn(),
      getRepositoryPolicy: vi.fn(),
      updateRepositoryPolicy: vi.fn(),
    },
  };
});

describe("RepositoryPolicyModal & RepositoriesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads and displays repository policy rules in modal", async () => {
    (apiClient.getRepositoryPolicy as any).mockResolvedValue({
      repository: "octocat/Hello-World",
      enabled: true,
      minimum_severity: "high",
      auto_remediate: true,
      auto_create_pr: true,
      target_branches: ["main", "staging"],
    });

    render(
      <RepositoryPolicyModal
        repository="octocat/Hello-World"
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    expect(screen.getByText("Loading policy rules...")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByTestId("policy-severity-select")).toHaveValue("high");
      expect(screen.getByTestId("policy-branches-input")).toHaveValue("main, staging");
    });
  });

  it("submits updated policy configuration to API", async () => {
    (apiClient.getRepositoryPolicy as any).mockResolvedValue({
      repository: "octocat/Hello-World",
      enabled: true,
      minimum_severity: "medium",
      auto_remediate: true,
      auto_create_pr: false,
      target_branches: ["main"],
    });
    (apiClient.updateRepositoryPolicy as any).mockResolvedValue({
      repository: "octocat/Hello-World",
      enabled: true,
      minimum_severity: "critical",
      auto_remediate: true,
      auto_create_pr: true,
      target_branches: ["main", "release/v1"],
    });

    const onSaved = vi.fn();
    render(
      <RepositoryPolicyModal
        repository="octocat/Hello-World"
        isOpen={true}
        onClose={vi.fn()}
        onSaved={onSaved}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId("policy-severity-select")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId("policy-severity-select"), {
      target: { value: "critical" },
    });
    fireEvent.change(screen.getByTestId("policy-branches-input"), {
      target: { value: "main, release/v1" },
    });

    fireEvent.click(screen.getByTestId("save-policy-btn"));

    await waitFor(() => {
      expect(apiClient.updateRepositoryPolicy).toHaveBeenCalledWith(
        "octocat",
        "Hello-World",
        expect.objectContaining({
          minimum_severity: "critical",
          target_branches: ["main", "release/v1"],
        })
      );
      expect(screen.getByText("Policy configuration updated successfully.")).toBeInTheDocument();
    });
  });

  it("renders repositories list and opens policy modal when policy button is clicked", async () => {
    (apiClient.getRepositories as any).mockResolvedValue({
      repositories: [
        {
          repository: "octocat/Hello-World",
          installation_status: "installed",
          total_jobs: 1,
          active_jobs: 0,
          verified_prs: 1,
          failed_jobs: 0,
          last_job_id: "job-deliv-alert-2",
          last_activity: "2026-08-25T18:04:27.296616+00:00",
        },
      ],
      total: 1,
    });
    (apiClient.getRepositoryPolicy as any).mockResolvedValue({
      repository: "octocat/Hello-World",
      enabled: true,
      minimum_severity: "high",
    });

    render(<RepositoriesPage />);

    await waitFor(() => {
      expect(screen.getByText("octocat/Hello-World")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("edit-policy-octocat/Hello-World"));

    await waitFor(() => {
      expect(screen.getByTestId("repository-policy-modal")).toBeInTheDocument();
    });
  });

  it("handles update policy error, displays error message, and leaves modal open", async () => {
    (apiClient.getRepositoryPolicy as any).mockResolvedValue({
      repository: "octocat/Hello-World",
      enabled: true,
      minimum_severity: "medium",
    });
    (apiClient.updateRepositoryPolicy as any).mockRejectedValue(
      new Error("Invalid minimum_severity 'invalid'.")
    );

    const onSaved = vi.fn();
    const onClose = vi.fn();

    render(
      <RepositoryPolicyModal
        repository="octocat/Hello-World"
        isOpen={true}
        onClose={onClose}
        onSaved={onSaved}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId("policy-severity-select")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("save-policy-btn"));

    await waitFor(() => {
      expect(screen.getByText("Invalid minimum_severity 'invalid'.")).toBeInTheDocument();
      expect(onSaved).not.toHaveBeenCalled();
      expect(onClose).not.toHaveBeenCalled();
      expect(screen.getByTestId("repository-policy-modal")).toBeInTheDocument();
    });
  });
});
