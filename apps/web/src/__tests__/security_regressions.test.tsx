import { describe, it, expect, vi } from "vitest";
import { isSafeGitHubUrl, PatchProofClient } from "@/lib/api";

describe("Security Invariants & URL Validation", () => {
  it("validates legitimate GitHub URLs and rejects unsafe schemes/domains", () => {
    expect(isSafeGitHubUrl("https://github.com/octocat/Hello-World/pull/42")).toBe(true);
    expect(isSafeGitHubUrl("https://github.com/patchproof/patchproof/pull/1")).toBe(true);
    expect(isSafeGitHubUrl("http://localhost:8000/jobs/1")).toBe(true);

    // Reject malicious schemas & domains
    expect(isSafeGitHubUrl("javascript:alert(document.cookie)")).toBe(false);
    expect(isSafeGitHubUrl("https://evil-phishing-site.com/github.com/pull/42")).toBe(false);
    expect(isSafeGitHubUrl("data:text/html,<script>alert(1)</script>")).toBe(false);
    expect(isSafeGitHubUrl("")).toBe(false);
    expect(isSafeGitHubUrl(null)).toBe(false);
    expect(isSafeGitHubUrl(undefined)).toBe(false);
  });

  it("ensures PatchProofClient handles 401 Unauthorized securely", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: () => Promise.resolve({ detail: "Invalid or expired API token" }),
    });

    const client = new PatchProofClient("http://localhost:8000", "bad-key");
    await expect(client.getJobs()).rejects.toThrow("Invalid or expired API token");
  });

  it("ensures PatchProofClient handles 408 Request Timeout cleanly", async () => {
    const abortError = new Error("The operation was aborted");
    abortError.name = "AbortError";
    global.fetch = vi.fn().mockRejectedValue(abortError);

    const client = new PatchProofClient("http://localhost:8000");
    await expect(client.getJobs()).rejects.toThrow("Request timed out");
  });
});
