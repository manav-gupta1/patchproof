import { describe, it, expect, vi, beforeEach } from "vitest";
import { PatchProofClient, ApiError, resolveApiBaseUrl } from "@/lib/api";

describe("PatchProofClient", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("attaches Authorization header and resolves data", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ jobs: [], total: 0 }),
    });
    global.fetch = mockFetch;

    const client = new PatchProofClient("http://localhost:8000", "test-api-token");
    const res = await client.getJobs();

    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:8000/jobs",
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer test-api-token",
        }),
      })
    );
    expect(res.jobs).toEqual([]);
  });

  it("throws structured ApiError on 404 or 401", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: () => Promise.resolve({ detail: "Job 'job-999' not found" }),
    });
    global.fetch = mockFetch;

    const client = new PatchProofClient("http://localhost:8000");

    await expect(client.getJob("job-999")).rejects.toThrow("Job 'job-999' not found");
  });

  it("stops polling on terminal states", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          job_id: "job-term",
          repository: "octocat/Hello-World",
          state: "pr_created",
          verified: true,
          events: [],
        }),
    });
    global.fetch = mockFetch;

    const client = new PatchProofClient("http://localhost:8000");
    const onUpdate = vi.fn();

    const stop = client.pollJob("job-term", onUpdate, undefined, 100);

    await new Promise((r) => setTimeout(r, 250));
    expect(onUpdate).toHaveBeenCalledTimes(1);
    stop();
  });

  it("normalizes Docker-internal 'api' service name to browser-accessible host", () => {
    const resolved = resolveApiBaseUrl("http://api:8000");
    expect(resolved).not.toContain("//api:");
    expect(resolved).toContain(":8000");
  });

  it("prioritizes window.__PATCHPROOF_API_URL__ override when available", () => {
    (window as any).__PATCHPROOF_API_URL__ = "https://custom-api.patchproof.io";
    const resolved = resolveApiBaseUrl();
    expect(resolved).toBe("https://custom-api.patchproof.io");
    delete (window as any).__PATCHPROOF_API_URL__;
  });
});
