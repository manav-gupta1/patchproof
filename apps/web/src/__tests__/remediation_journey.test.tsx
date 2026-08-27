import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent, act } from "@testing-library/react";
import { apiClient, ApiError } from "@/lib/api";
import JobDetailPage from "@/app/jobs/[jobId]/page";
import { TriggerRemediationModal } from "@/components/repositories/TriggerRemediationModal";
import { JobStatusResponse, JobEvidenceResponse } from "@/lib/types";

// Mock next/navigation
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useParams: () => ({ jobId: "job-test-123" }),
  useRouter: () => ({ push: mockPush }),
}));

describe("End-to-End Remediation Journey", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("submits remediation, receives immediate QUEUED state, and redirects to /jobs/{job_id}", async () => {
    const triggerSpy = vi.spyOn(apiClient, "triggerRemediation").mockResolvedValue({
      job_id: "job-test-e2e-001",
      repository: "octocat/Hello-World",
      commit_sha: "main",
      state: "queued",
      verified: false,
    });

    const onClose = vi.fn();
    render(
      <TriggerRemediationModal
        isOpen={true}
        onClose={onClose}
        repository="octocat/Hello-World"
      />
    );

    const submitBtn = screen.getByTestId("submit-remediation-button");
    await act(async () => {
      fireEvent.click(submitBtn);
    });

    expect(triggerSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        repository: "octocat/Hello-World",
        commit_sha: "main",
        rule_id: "python.sql-injection",
        severity: "HIGH",
        auto_create_pr: true,
      })
    );

    expect(mockPush).toHaveBeenCalledWith("/jobs/job-test-e2e-001");
    expect(onClose).toHaveBeenCalled();
  });

  it("handles 400 validation error in remediation submission with human-readable banner", async () => {
    vi.spyOn(apiClient, "triggerRemediation").mockRejectedValue(
      new ApiError(400, "Branch 'invalid-branch' not found in repository")
    );

    render(
      <TriggerRemediationModal
        isOpen={true}
        onClose={vi.fn()}
        repository="octocat/Hello-World"
      />
    );

    const submitBtn = screen.getByTestId("submit-remediation-button");
    await act(async () => {
      fireEvent.click(submitBtn);
    });

    expect(await screen.findByText(/Validation Error: Branch 'invalid-branch' not found/i)).toBeInTheDocument();
  });

  it("handles 403 authorization error in remediation submission", async () => {
    vi.spyOn(apiClient, "triggerRemediation").mockRejectedValue(
      new ApiError(403, "Tenant 'alpha' is not authorized to remediate repository 'octocat/Hello-World'")
    );

    render(
      <TriggerRemediationModal
        isOpen={true}
        onClose={vi.fn()}
        repository="octocat/Hello-World"
      />
    );

    const submitBtn = screen.getByTestId("submit-remediation-button");
    await act(async () => {
      fireEvent.click(submitBtn);
    });

    expect(await screen.findByText(/Authorization Error: Tenant 'alpha' is not authorized/i)).toBeInTheDocument();
  });

  it("handles 500 broker / queue error in remediation submission", async () => {
    vi.spyOn(apiClient, "triggerRemediation").mockRejectedValue(
      new ApiError(500, "Celery broker unreachable")
    );

    render(
      <TriggerRemediationModal
        isOpen={true}
        onClose={vi.fn()}
        repository="octocat/Hello-World"
      />
    );

    const submitBtn = screen.getByTestId("submit-remediation-button");
    await act(async () => {
      fireEvent.click(submitBtn);
    });

    expect(await screen.findByText(/Queue \/ Server Error: Celery broker unreachable/i)).toBeInTheDocument();
  });

  it("hydrates queued job from persistent JobRecord and displays live SSE state", async () => {
    const queuedJob: JobStatusResponse = {
      job_id: "job-test-123",
      repository: "octocat/Hello-World",
      commit_sha: "a1b2c3d4e5f6",
      event_type: "code_scanning_alert",
      state: "queued",
      verified: false,
      is_stale: false,
      events: [
        {
          id: 1,
          from_state: null,
          to_state: "queued",
          message: "Created from direct finding submission",
          created_at: new Date().toISOString(),
        },
      ],
    };

    vi.spyOn(apiClient, "getJob").mockResolvedValue(queuedJob);
    vi.spyOn(apiClient, "getJobEvidence").mockResolvedValue(null as any);

    let sseCallbacks: any = null;
    vi.spyOn(apiClient, "subscribeToJobEvents").mockImplementation((jobId, callbacks) => {
      sseCallbacks = callbacks;
      return () => {};
    });

    render(<JobDetailPage />);

    // Check initial queued hydration
    expect(await screen.findByTestId("job-detail-page")).toBeInTheDocument();
    expect(screen.getByText("octocat/Hello-World")).toBeInTheDocument();
    expect(screen.getByText("REMEDIATION IN PROGRESS")).toBeInTheDocument();

    // Trigger SSE transition to analyzing
    await act(async () => {
      if (sseCallbacks?.onEvent) {
        sseCallbacks.onEvent({
          job_id: "job-test-123",
          event_id: 2,
          from_state: "queued",
          to_state: "analyzing",
          message: "AST syntax analysis",
          created_at: new Date().toISOString(),
        });
      }
    });

    // Check that timeline and stepper reflect analyzing
    expect(screen.getByText("AST syntax validated")).toBeInTheDocument();
  });

  it("displays RECONNECTING... status when SSE connection drops and reconnects", async () => {
    const activeJob: JobStatusResponse = {
      job_id: "job-test-123",
      repository: "octocat/Hello-World",
      commit_sha: "a1b2c3d4e5f6",
      event_type: "code_scanning_alert",
      state: "verifying",
      verified: false,
      is_stale: false,
      events: [],
    };

    vi.spyOn(apiClient, "getJob").mockResolvedValue(activeJob);
    vi.spyOn(apiClient, "getJobEvidence").mockResolvedValue(null as any);

    let sseCallbacks: any = null;
    vi.spyOn(apiClient, "subscribeToJobEvents").mockImplementation((jobId, callbacks) => {
      sseCallbacks = callbacks;
      return () => {};
    });

    render(<JobDetailPage />);

    await waitFor(() => {
      expect(screen.getByTestId("sse-status-indicator")).toBeInTheDocument();
    });

    // Trigger reconnection event
    await act(async () => {
      if (sseCallbacks?.onReconnecting) {
        sseCallbacks.onReconnecting();
      }
    });

    expect(screen.getByText(/RECONNECTING…/i)).toBeInTheDocument();

    // Trigger connection re-open
    await act(async () => {
      if (sseCallbacks?.onOpen) {
        sseCallbacks.onOpen();
      }
    });

    expect(screen.getByText(/SSE Connected/i)).toBeInTheDocument();
  });

  it("renders verified path with green gates, cryptographic proof, and PR details", async () => {
    const verifiedJob: JobStatusResponse = {
      job_id: "job-test-123",
      repository: "octocat/Hello-World",
      commit_sha: "a1b2c3d4e5f6",
      event_type: "code_scanning_alert",
      state: "pr_created",
      verified: true,
      pr_number: 42,
      pr_url: "https://github.com/octocat/Hello-World/pull/42",
      is_stale: false,
      events: [
        { id: 1, from_state: null, to_state: "queued", message: "Queued" },
        { id: 2, from_state: "queued", to_state: "scanning", message: "Scanning" },
        { id: 3, from_state: "scanning", to_state: "patching", message: "Patched" },
        { id: 4, from_state: "patching", to_state: "verifying", message: "Verified in gVisor" },
        { id: 5, from_state: "verifying", to_state: "verified", message: "Signed" },
        { id: 6, from_state: "verified", to_state: "pr_created", message: "PR #42 created" },
      ],
    };

    const verifiedEvidence: JobEvidenceResponse = {
      evidence_id: "ev-12345",
      job_id: "job-test-123",
      commit_sha: "a1b2c3d4e5f6",
      repository: "octocat/Hello-World",
      verified: true,
      finding_count: 1,
      signature: "ed25519_sig_valid_123",
      signing_key_id: "key-prod-01",
      verification_results: {
        rescan_findings_count: 0,
        target_vulnerability_eliminated: true,
        verification_status: "passed",
      },
    };

    vi.spyOn(apiClient, "getJob").mockResolvedValue(verifiedJob);
    vi.spyOn(apiClient, "getJobEvidence").mockResolvedValue(verifiedEvidence);
    vi.spyOn(apiClient, "subscribeToJobEvents").mockImplementation(() => () => {});

    render(<JobDetailPage />);

    expect(await screen.findByTestId("safety-banner-verified")).toBeInTheDocument();
    expect(screen.getByText("VERIFIED → SAFE TO PUBLISH")).toBeInTheDocument();
    expect(screen.getByText("Safe for GitHub publication")).toBeInTheDocument();
  });

  it("renders failed verification path strictly with fail-closed banner, halting at failing gate and zero writes", async () => {
    const failedJob: JobStatusResponse = {
      job_id: "job-test-123",
      repository: "octocat/Hello-World",
      commit_sha: "a1b2c3d4e5f6",
      event_type: "code_scanning_alert",
      state: "failed",
      verified: false,
      error: "Verification failed: regression tests failed with exit code 1",
      is_stale: false,
      events: [
        { id: 1, from_state: null, to_state: "queued", message: "Queued" },
        { id: 2, from_state: "queued", to_state: "scanning", message: "Scanning" },
        { id: 3, from_state: "scanning", to_state: "patching", message: "Patched" },
        { id: 4, from_state: "patching", to_state: "verifying", message: "Running tests in gVisor" },
        { id: 5, from_state: "verifying", to_state: "failed", message: "Verification failed: regression tests failed" },
      ],
    };

    vi.spyOn(apiClient, "getJob").mockResolvedValue(failedJob);
    vi.spyOn(apiClient, "getJobEvidence").mockResolvedValue(null as any);
    vi.spyOn(apiClient, "subscribeToJobEvents").mockImplementation(() => () => {});

    render(<JobDetailPage />);

    expect(await screen.findByTestId("safety-banner-failed")).toBeInTheDocument();
    expect(screen.getByText("UNVERIFIED → ZERO GITHUB WRITES (PUBLICATION BLOCKED)")).toBeInTheDocument();
    expect(screen.getAllByText(/regression tests failed with exit code 1/i)[0]).toBeInTheDocument();
    expect(screen.getByText("Zero GitHub writes (blocked)")).toBeInTheDocument();
  });

  it("renders policy blocked path halting at policy gate with zero GitHub writes", async () => {
    const policyBlockedJob: JobStatusResponse = {
      job_id: "job-test-123",
      repository: "octocat/Hello-World",
      commit_sha: "a1b2c3d4e5f6",
      event_type: "code_scanning_alert",
      state: "failed",
      verified: false,
      error: "Policy rejection: production branch requires human approval",
      policy: {
        allowed: false,
        action: "block",
        reason: "production branch requires human approval",
      },
      is_stale: false,
      events: [
        { id: 1, from_state: null, to_state: "queued", message: "Queued" },
        { id: 2, from_state: "queued", to_state: "scanning", message: "Scanning" },
        { id: 3, from_state: "scanning", to_state: "failed", message: "Policy blocked: human approval required" },
      ],
    };

    vi.spyOn(apiClient, "getJob").mockResolvedValue(policyBlockedJob);
    vi.spyOn(apiClient, "getJobEvidence").mockResolvedValue(null as any);
    vi.spyOn(apiClient, "subscribeToJobEvents").mockImplementation(() => () => {});

    render(<JobDetailPage />);

    expect(await screen.findByTestId("safety-banner-failed")).toBeInTheDocument();
    expect(screen.getAllByText(/Policy rejection: production branch requires human approval/i)[0]).toBeInTheDocument();
  });
});
