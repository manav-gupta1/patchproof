import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { EvidenceCard } from "@/components/jobs/EvidenceCard";
import { VerificationCard } from "@/components/jobs/VerificationCard";
import { PolicyCard } from "@/components/jobs/PolicyCard";
import { FindingCard } from "@/components/jobs/FindingCard";
import { DiffViewer } from "@/components/jobs/DiffViewer";
import { apiClient } from "@/lib/api";
import { JobEvidenceResponse } from "@/lib/types";

describe("EvidenceCard", () => {
  const mockEvidence: JobEvidenceResponse = {
    evidence_id: "ev-job-001",
    job_id: "job-001",
    commit_sha: "e".repeat(40),
    repository: "acme/target-repo",
    verified: true,
    finding_count: 1,
    sha256_digest: "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
    signing_key_id: "patchproof-dev-key-1",
    signing_algorithm: "ed25519",
    signed_at: "2026-08-25T12:00:00Z",
  };

  it("renders cryptographic details and verifies signature", async () => {
    vi.spyOn(apiClient, "verifyEvidence").mockResolvedValue({
      valid: true,
      key_id: "patchproof-dev-key-1",
      signing_algorithm: "ed25519",
      sha256_digest: mockEvidence.sha256_digest,
    });

    render(<EvidenceCard evidence={mockEvidence} />);

    expect(screen.getByTestId("evidence-card")).toBeInTheDocument();
    expect(screen.getByText("ev-job-001")).toBeInTheDocument();
    expect(screen.getByText(/Evidence is cryptographically bound to this verification/)).toBeInTheDocument();

    const verifyBtn = screen.getByRole("button", { name: /Verify Signature/i });
    fireEvent.click(verifyBtn);

    await waitFor(() => {
      expect(screen.getByText(/Ed25519 digital signature and canonical SHA-256 digest verified successfully/)).toBeInTheDocument();
    });
  });
});

describe("VerificationCard", () => {
  it("renders verification results, gVisor runtime and network policy", () => {
    render(
      <VerificationCard
        verified={true}
        verifiedSha="abc12345"
        results={{
          rescan_findings_count: 0,
          target_vulnerability_eliminated: true,
          verification_status: "passed",
          test_summary: "Tests passed in gVisor sandbox.",
          sandbox_provider: "gVisor",
          network_policy: "Denied",
          execution_duration_sec: 4.8,
        }}
      />
    );

    expect(screen.getByTestId("verification-card")).toBeInTheDocument();
    expect(screen.getByText("gVisor")).toBeInTheDocument();
    expect(screen.getByText("Denied")).toBeInTheDocument();
    expect(screen.getByText("4.8s")).toBeInTheDocument();
    expect(screen.getByText("✓ PASSED")).toBeInTheDocument();
  });
});

describe("PolicyCard", () => {
  it("renders policy decision allowed", () => {
    render(
      <PolicyCard
        policy={{
          allowed: true,
          action: "remediate_and_publish",
          reason: "Target vulnerability exceeds minimum severity threshold.",
          target_branch: "main",
        }}
      />
    );

    expect(screen.getByTestId("policy-card")).toBeInTheDocument();
    expect(screen.getByText("✓ ALLOWED")).toBeInTheDocument();
    expect(screen.getByText(/Target vulnerability exceeds minimum severity threshold/)).toBeInTheDocument();
  });
});

describe("FindingCard", () => {
  it("renders finding rule ID and severity badge", () => {
    render(
      <FindingCard
        finding={{
          rule_id: "python.lang.security.injection.sql-injection",
          fingerprint: "fp-sqli-001",
          severity: "HIGH",
          file: "app/database.py",
          line: 42,
          scanner: "Semgrep SAST",
          description: "Unparameterized SQL string format execution detected.",
        }}
      />
    );

    expect(screen.getByTestId("finding-card")).toBeInTheDocument();
    expect(screen.getByText("python.lang.security.injection.sql-injection")).toBeInTheDocument();
    expect(screen.getByText("HIGH")).toBeInTheDocument();
    expect(screen.getByText("app/database.py:42")).toBeInTheDocument();
  });
});

describe("DiffViewer", () => {
  it("renders patch applied in isolated workspace notice", () => {
    render(
      <DiffViewer
        patch={{
          title: "fix(security): sanitize user input",
          files_changed: ["app/database.py"],
          diff: "--- a/app/database.py\n+++ b/app/database.py\n@@ -1,3 +1,3 @@\n-db.execute(f'SELECT * FROM users WHERE id = {user_id}')\n+db.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
        }}
      />
    );

    expect(screen.getByTestId("diff-viewer")).toBeInTheDocument();
    expect(screen.getByText("Patch generated")).toBeInTheDocument();
    expect(screen.getByText("Patch applied only in isolated workspace")).toBeInTheDocument();
    expect(screen.getByText("app/database.py")).toBeInTheDocument();
  });
});
