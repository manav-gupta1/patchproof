import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import { TriggerRemediationModal } from "@/components/repositories/TriggerRemediationModal";
import RepositoriesPage from "@/app/repositories/page";
import { LiveConsoleSection } from "@/components/dashboard/LiveConsoleSection";
import { apiClient } from "@/lib/api";
const mockPush = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
  }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(),
  useParams: () => ({ jobId: "job-001" }),
}));

vi.mock("@/lib/api", () => {
  return {
    apiClient: {
      getRepositories: vi.fn(),
      triggerRemediation: vi.fn(),
      getJobs: vi.fn(),
      getSystemStatus: vi.fn(),
      subscribeToAllEvents: vi.fn(() => vi.fn()),
    },
  };
});

describe("TriggerRemediationModal & Page Integrations", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders TriggerRemediationModal when open and shows repository name", () => {
    render(
      <TriggerRemediationModal
        isOpen={true}
        onClose={vi.fn()}
        repository="octocat/Hello-World"
      />
    );

    expect(screen.getByText("Trigger Automated Remediation")).toBeInTheDocument();
    expect(screen.getByText("octocat/Hello-World")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Run Remediation" })).toBeInTheDocument();
  });

  it("submits the correct request payload on trigger", async () => {
    vi.mocked(apiClient.triggerRemediation).mockResolvedValue({
      job_id: "job-remediation-123",
      repository: "octocat/Hello-World",
    });

    render(
      <TriggerRemediationModal
        isOpen={true}
        onClose={vi.fn()}
        repository="octocat/Hello-World"
      />
    );

    const submitBtn = screen.getByRole("button", { name: "Run Remediation" });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(apiClient.triggerRemediation).toHaveBeenCalledWith({
        repository: "octocat/Hello-World",
        commit_sha: "main",
        file: "app.py",
        start_line: 1,
        end_line: 1,
        rule_id: "python.sql-injection",
        severity: "HIGH",
        message: "SQL injection in query construction",
        code_snippet: 'query = f"SELECT * FROM users WHERE username = \'{user_input}\'"',
        auto_create_pr: true,
      });
      expect(mockPush).toHaveBeenCalledWith("/jobs/job-remediation-123");
    });
  });

  it("handles empty repository and displays appropriate message/restriction", async () => {
    vi.mocked(apiClient.getRepositories).mockResolvedValue({
      repositories: [],
    });

    render(
      <TriggerRemediationModal
        isOpen={true}
        onClose={vi.fn()}
        repository={null}
      />
    );

    await waitFor(() => {
      expect(
        screen.getByText("No active repositories connected. Onboard one first on the repositories tab.")
      ).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Run Remediation" })).toBeDisabled();
    });
  });

  it("handles API trigger failure and displays the error message", async () => {
    vi.mocked(apiClient.triggerRemediation).mockRejectedValue(new Error("Vulnerable repository branch is locked"));

    render(
      <TriggerRemediationModal
        isOpen={true}
        onClose={vi.fn()}
        repository="octocat/Hello-World"
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "Run Remediation" }));

    await waitFor(() => {
      expect(screen.getByText("Vulnerable repository branch is locked")).toBeInTheDocument();
      expect(mockPush).not.toHaveBeenCalled();
    });
  });

  it("disables buttons and shows loading state during submission to prevent double clicks", async () => {
    let resolvePromise: any;
    const promise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    vi.mocked(apiClient.triggerRemediation).mockReturnValue(promise);

    render(
      <TriggerRemediationModal
        isOpen={true}
        onClose={vi.fn()}
        repository="octocat/Hello-World"
      />
    );

    const submitBtn = screen.getByRole("button", { name: "Run Remediation" });
    fireEvent.click(submitBtn);

    expect(submitBtn).toBeDisabled();
    expect(screen.getByText("Running Pipeline...")).toBeInTheDocument();

    await act(async () => {
      resolvePromise({ job_id: "job-1" });
      await promise;
    });
  });

  it("renders Remediate button in RepositoriesPage cards", async () => {
    vi.mocked(apiClient.getRepositories).mockResolvedValue({
      repositories: [
        {
          repository: "octocat/Hello-World",
          installation_status: "installed",
          total_jobs: 1,
          active_jobs: 0,
          verified_prs: 1,
          failed_jobs: 0,
          last_job_id: "job-1",
          last_activity: new Date().toISOString(),
        },
      ],
    });

    render(<RepositoriesPage />);

    await waitFor(() => {
      expect(screen.getByTestId("remediate-octocat/Hello-World")).toBeInTheDocument();
    });

    // Clicking it opens the modal
    fireEvent.click(screen.getByTestId("remediate-octocat/Hello-World"));
    expect(screen.getByText("Trigger Automated Remediation")).toBeInTheDocument();
  });

  it("renders Run Remediation button in LiveConsoleSection and triggers modal", async () => {
    vi.mocked(apiClient.getJobs).mockResolvedValue({ jobs: [] });
    vi.mocked(apiClient.getSystemStatus).mockResolvedValue({
      api: "healthy",
      worker: "healthy",
      database: "healthy",
      broker: "healthy",
    });
    vi.mocked(apiClient.getRepositories).mockResolvedValue({
      repositories: [
        { repository: "acme/api", installation_status: "installed", total_jobs: 0, active_jobs: 0, verified_prs: 0, failed_jobs: 0, last_activity: "" },
      ],
    });

    render(<LiveConsoleSection />);

    await waitFor(() => {
      expect(screen.getByTestId("run-remediation-console-btn")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("run-remediation-console-btn"));
    await waitFor(() => {
      expect(screen.getByText("Trigger Automated Remediation")).toBeInTheDocument();
    });
  });
});


