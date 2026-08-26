import { describe, it, expect, vi, beforeEach } from "vitest";
import { PatchProofClient } from "@/lib/api";
import { JobStateEvent, JobTerminalEvent } from "@/lib/types";

describe("PatchProofClient SSE Subscription", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("subscribes to SSE stream and dispatches job_state and job_terminal events", async () => {
    const encoder = new TextEncoder();
    const mockStream = new ReadableStream({
      start(controller) {
        // Yield job_state frame
        const statePayload: JobStateEvent = {
          job_id: "job-sse-test",
          event_id: 1,
          from_state: "queued",
          to_state: "scanning",
          message: "Cloned source repository",
          created_at: "2026-08-25T10:00:00Z",
        };
        controller.enqueue(
          encoder.encode(`id: 1\nevent: job_state\ndata: ${JSON.stringify(statePayload)}\n\n`)
        );

        // Yield job_terminal frame
        const termPayload: JobTerminalEvent = {
          job_id: "job-sse-test",
          state: "pr_created",
          error: null,
          pr_number: 99,
          pr_url: "https://github.com/octocat/Hello-World/pull/99",
          is_stale: false,
        };
        controller.enqueue(
          encoder.encode(`id: 2\nevent: job_terminal\ndata: ${JSON.stringify(termPayload)}\n\n`)
        );

        controller.close();
      },
    });

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: mockStream,
      headers: new Headers({ "content-type": "text/event-stream" }),
    });

    const client = new PatchProofClient("http://localhost:8000", "test-token");
    const onEvent = vi.fn();
    const onTerminal = vi.fn();
    const onOpen = vi.fn();
    const onClose = vi.fn();

    const unsubscribe = client.subscribeToJobEvents("job-sse-test", {
      onOpen,
      onEvent,
      onTerminal,
      onClose,
    });

    await new Promise((r) => setTimeout(r, 100));

    expect(onOpen).toHaveBeenCalled();
    expect(onEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        job_id: "job-sse-test",
        to_state: "scanning",
      })
    );
    expect(onTerminal).toHaveBeenCalledWith(
      expect.objectContaining({
        job_id: "job-sse-test",
        state: "pr_created",
        pr_number: 99,
      })
    );

    unsubscribe();
  });

  it("passes Last-Event-ID header and Authorization bearer token", async () => {
    const encoder = new TextEncoder();
    const mockStream = new ReadableStream({
      start(controller) {
        controller.close();
      },
    });

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      body: mockStream,
    });
    global.fetch = mockFetch;

    const client = new PatchProofClient("http://localhost:8000", "secret-bearer-key");
    const unsubscribe = client.subscribeToJobEvents(
      "job-test-headers",
      {},
      { lastEventId: 4 }
    );

    await new Promise((r) => setTimeout(r, 50));

    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:8000/jobs/job-test-headers/events",
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer secret-bearer-key",
          "Last-Event-ID": "4",
          Accept: "text/event-stream",
        }),
      })
    );

    unsubscribe();
  });

  it("falls back to polling when SSE connection fails", async () => {
    // Fail SSE fetch
    global.fetch = vi.fn().mockRejectedValue(new Error("SSE Network failed"));

    const client = new PatchProofClient("http://localhost:8000");
    const pollSpy = vi.spyOn(client, "pollJob").mockReturnValue(() => {});
    const onFallback = vi.fn();

    const unsubscribe = client.subscribeToJobEvents(
      "job-fallback-test",
      { onFallback },
      { maxRetries: 0, fallbackToPolling: true }
    );

    await new Promise((r) => setTimeout(r, 100));

    expect(onFallback).toHaveBeenCalled();
    expect(pollSpy).toHaveBeenCalledWith("job-fallback-test", expect.any(Function), undefined);

    unsubscribe();
  });
});
