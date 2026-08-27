import {
  JobStatusResponse,
  JobEvidenceResponse,
  JobListResponse,
  RepositoryListResponse,
  SystemStatusResponse,
  SettingsStatusResponse,
  EvidenceVerificationResult,
  JobStateEvent,
  JobTerminalEvent,
  JobTransitionEvent,
  RemediationTriggerRequest,
  RemediationTriggerResponse,
} from "./types";

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

export interface FetchOptions extends RequestInit {
  apiKey?: string;
  timeoutMs?: number;
}

export function isSafeGitHubUrl(url?: string | null): boolean {
  if (!url || typeof url !== "string") return false;
  const trimmed = url.trim();
  // Strictly enforce official GitHub PR URLs or secure localhost staging
  if (trimmed.startsWith("https://github.com/")) {
    try {
      const parsed = new URL(trimmed);
      return parsed.hostname === "github.com" && parsed.pathname.length > 1;
    } catch {
      return false;
    }
  }
  if (trimmed.startsWith("http://localhost:") || trimmed.startsWith("http://127.0.0.1:")) {
    return true;
  }
  return false;
}

export interface SseSubscriptionCallbacks {
  onEvent?: (event: JobStateEvent) => void;
  onTerminal?: (event: JobTerminalEvent) => void;
  onError?: (error: Error) => void;
  onOpen?: () => void;
  onClose?: () => void;
  onReconnecting?: () => void;
  onFallback?: () => void;
}

export interface SseSubscriptionOptions {
  lastEventId?: number;
  maxRetries?: number;
  fallbackToPolling?: boolean;
}

export function resolveApiBaseUrl(customUrl?: string): string {
  if (typeof window !== "undefined") {
    const win = window as any;
    if (win.__PATCHPROOF_API_URL__ && typeof win.__PATCHPROOF_API_URL__ === "string" && win.__PATCHPROOF_API_URL__.trim()) {
      return normalizeBrowserUrl(win.__PATCHPROOF_API_URL__.trim());
    }
    if (customUrl && customUrl.trim()) {
      return normalizeBrowserUrl(customUrl.trim());
    }
    const envUrl = process.env.NEXT_PUBLIC_API_URL;
    if (envUrl && envUrl.trim()) {
      return normalizeBrowserUrl(envUrl.trim());
    }
    const host = window.location.hostname || "localhost";
    const protocol = window.location.protocol || "http:";
    return `${protocol}//${host}:8000`;
  }

  return (
    customUrl ||
    process.env.INTERNAL_API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://localhost:8000"
  );
}

function normalizeBrowserUrl(url: string): string {
  if (typeof window === "undefined") return url;
  if (url.includes("//api:") || url === "http://api:8000" || url === "https://api:8000") {
    const host = window.location.hostname || "localhost";
    return url.replace("//api:", `//${host}:`);
  }
  return url;
}

export class PatchProofClient {
  private customBaseUrl?: string;
  private apiKey: string | null;

  constructor(baseUrl?: string, apiKey?: string) {
    this.customBaseUrl = baseUrl;
    if (typeof window !== "undefined") {
      this.apiKey =
        apiKey ||
        (window as any).__PATCHPROOF_API_KEY__ ||
        process.env.NEXT_PUBLIC_API_KEY ||
        "patchproof_dev_api_key";
    } else {
      this.apiKey =
        apiKey ||
        process.env.PATCHPROOF_API_KEY ||
        process.env.NEXT_PUBLIC_API_KEY ||
        "patchproof_dev_api_key";
    }
  }

  public getBaseUrl(): string {
    return resolveApiBaseUrl(this.customBaseUrl);
  }

  private async request<T>(path: string, options: FetchOptions = {}): Promise<T> {
    const { apiKey, timeoutMs = 15000, headers = {}, ...fetchOpts } = options;
    const resolvedKey = apiKey !== undefined ? apiKey : this.apiKey;

    const requestHeaders: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(headers as Record<string, string>),
    };

    if (resolvedKey) {
      requestHeaders["Authorization"] = `Bearer ${resolvedKey}`;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const activeBaseUrl = this.getBaseUrl();
      const url = `${activeBaseUrl.replace(/\/$/, "")}${path}`;
      const response = await fetch(url, {
        ...fetchOpts,
        headers: requestHeaders,
        signal: controller.signal,
      });

      if (!response.ok) {
        let errorData: any = null;
        let errorMessage = `API Request failed with status ${response.status}`;
        try {
          errorData = await response.json();
          if (errorData?.detail) {
            errorMessage = typeof errorData.detail === "string"
              ? errorData.detail
              : JSON.stringify(errorData.detail);
          }
        } catch {
          // ignore non-json error
        }
        throw new ApiError(response.status, errorMessage, errorData);
      }

      return (await response.json()) as T;
    } catch (err: any) {
      if (err.name === "AbortError") {
        throw new ApiError(408, "Request timed out");
      }
      if (err instanceof ApiError) {
        throw err;
      }
      throw new ApiError(0, err.message || "Network error connecting to PatchProof API");
    } finally {
      clearTimeout(timeoutId);
    }
  }

  async getJobs(params?: {
    repository?: string;
    state?: string;
    limit?: number;
    offset?: number;
  }): Promise<JobListResponse> {
    const query = new URLSearchParams();
    if (params?.repository) query.set("repository", params.repository);
    if (params?.state) query.set("state", params.state);
    if (params?.limit) query.set("limit", String(params.limit));
    if (params?.offset) query.set("offset", String(params.offset));

    const queryString = query.toString();
    const path = `/jobs${queryString ? `?${queryString}` : ""}`;
    return this.request<JobListResponse>(path);
  }

  async getJob(jobId: string): Promise<JobStatusResponse> {
    if (!jobId) throw new Error("jobId is required");
    return this.request<JobStatusResponse>(`/jobs/${encodeURIComponent(jobId)}`);
  }

  async getJobEvidence(jobId: string): Promise<JobEvidenceResponse> {
    if (!jobId) throw new Error("jobId is required");
    return this.request<JobEvidenceResponse>(`/jobs/${encodeURIComponent(jobId)}/evidence`);
  }

  async getEvidenceExport(jobId: string): Promise<any> {
    if (!jobId) throw new Error("jobId is required");
    return this.request<any>(`/jobs/${encodeURIComponent(jobId)}/evidence/export`);
  }

  exportEvidenceUrl(jobId: string): string {
    return `${this.getBaseUrl().replace(/\/$/, "")}/jobs/${encodeURIComponent(jobId)}/evidence/export`;
  }

  async getRepositoryPolicy(owner: string, repo: string): Promise<any> {
    return this.request<any>(`/repositories/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}/policy`);
  }

  async updateRepositoryPolicy(owner: string, repo: string, policy: any): Promise<any> {
    return this.request<any>(`/repositories/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}/policy`, {
      method: "PUT",
      body: JSON.stringify(policy),
    });
  }

  async verifyEvidence(payload: Record<string, any>): Promise<EvidenceVerificationResult> {
    return this.request<EvidenceVerificationResult>("/evidence/verify", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async getRepositories(): Promise<RepositoryListResponse> {
    return this.request<RepositoryListResponse>("/repositories");
  }

  async onboardRepository(payload: {
    repository: string;
    default_branch?: string;
    installation_id?: number;
    status?: string;
    provider?: string;
    policy?: Record<string, any>;
  }): Promise<any> {
    return this.request<any>("/repositories", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async triggerRemediation(payload: RemediationTriggerRequest): Promise<RemediationTriggerResponse> {
    return this.request<RemediationTriggerResponse>("/remediations/run", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async getSystemStatus(): Promise<SystemStatusResponse> {
    return this.request<SystemStatusResponse>("/system/status");
  }

  async getSettingsStatus(): Promise<SettingsStatusResponse> {
    return this.request<SettingsStatusResponse>("/settings/status");
  }

  pollJob(
    jobId: string,
    onUpdate: (job: JobStatusResponse) => void,
    onError?: (err: Error) => void,
    baseIntervalMs: number = 2000
  ): () => void {
    let active = true;
    let timeoutId: any = null;
    let currentInterval = baseIntervalMs;
    let consecutiveErrors = 0;

    const terminalStates = new Set([
      "pr_created",
      "pr_merged",
      "pr_closed",
      "failed",
      "superseded",
      "rolled_back",
    ]);

    const executePoll = async () => {
      if (!active) return;

      // Pause when tab is inactive / hidden to prevent hammering API
      if (typeof document !== "undefined" && document.hidden) {
        return;
      }

      try {
        const job = await this.getJob(jobId);
        if (!active) return;
        onUpdate(job);

        consecutiveErrors = 0;
        currentInterval = baseIntervalMs;

        const stateLower = (job.state || "").toLowerCase();
        if (terminalStates.has(stateLower)) {
          active = false;
          return;
        }
      } catch (err: any) {
        if (!active) return;
        consecutiveErrors++;
        // Exponential backoff up to 15 seconds
        currentInterval = Math.min(baseIntervalMs * Math.pow(1.5, consecutiveErrors), 15000);
        if (onError) onError(err);
      }

      if (active) {
        timeoutId = setTimeout(executePoll, currentInterval);
      }
    };

    // Listen for tab focus/visibility change to immediately refresh
    const handleVisibilityChange = () => {
      if (!active) return;
      if (typeof document !== "undefined" && !document.hidden) {
        if (timeoutId) clearTimeout(timeoutId);
        executePoll();
      }
    };

    if (typeof document !== "undefined") {
      document.addEventListener("visibilitychange", handleVisibilityChange);
    }

    executePoll();

    return () => {
      active = false;
      if (timeoutId) clearTimeout(timeoutId);
      if (typeof document !== "undefined") {
        document.removeEventListener("visibilitychange", handleVisibilityChange);
      }
    };
  }

  /**
   * Subscribe to real-time Server-Sent Events (SSE) for a remediation job.
   * Uses authenticated streaming fetch without exposing credentials in query parameters.
   * Automatically falls back to polling if SSE is unsupported or fails repeatedly.
   */
  subscribeToJobEvents(
    jobId: string,
    callbacks: SseSubscriptionCallbacks,
    options: SseSubscriptionOptions = {}
  ): () => void {
    const { maxRetries = 3, fallbackToPolling = true } = options;
    let active = true;
    let abortController: AbortController | null = null;
    let retryCount = 0;
    let lastSeenEventId = options.lastEventId || 0;
    let fallbackUnpoll: (() => void) | null = null;
    let reconnectTimeoutId: any = null;

    const startStreaming = async () => {
      if (!active) return;

      abortController = new AbortController();
      const requestHeaders: Record<string, string> = {
        Accept: "text/event-stream",
        "Cache-Control": "no-cache",
      };

      if (this.apiKey) {
        requestHeaders["Authorization"] = `Bearer ${this.apiKey}`;
      }
      if (lastSeenEventId > 0) {
        requestHeaders["Last-Event-ID"] = String(lastSeenEventId);
      }

      try {
        const url = `${this.getBaseUrl().replace(/\/$/, "")}/jobs/${encodeURIComponent(jobId)}/events`;
        const response = await fetch(url, {
          headers: requestHeaders,
          signal: abortController.signal,
        });

        if (!response.ok) {
          throw new ApiError(response.status, `SSE connection failed with status ${response.status}`);
        }

        if (!response.body) {
          throw new Error("Streaming body not available in response");
        }

        retryCount = 0;
        if (callbacks.onOpen) callbacks.onOpen();

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (active) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const frames = buffer.split("\n\n");
          buffer = frames.pop() || "";

          for (const frame of frames) {
            if (!frame.trim() || frame.startsWith(":")) continue;

            const lines = frame.split("\n");
            let eventName = "message";
            let eventId: number | null = null;
            let dataStr = "";

            for (const line of lines) {
              if (line.startsWith("event: ")) {
                eventName = line.slice(7).trim();
              } else if (line.startsWith("id: ")) {
                try {
                  eventId = parseInt(line.slice(4).trim(), 10);
                  if (!isNaN(eventId)) {
                    lastSeenEventId = Math.max(lastSeenEventId, eventId);
                  }
                } catch {
                  // ignore invalid id
                }
              } else if (line.startsWith("data: ")) {
                dataStr = line.slice(6).trim();
              }
            }

            if (dataStr) {
              try {
                const parsedData = JSON.parse(dataStr);
                if (eventName === "job_state") {
                  if (callbacks.onEvent) callbacks.onEvent(parsedData as JobStateEvent);
                } else if (eventName === "job_terminal") {
                  active = false;
                  if (callbacks.onTerminal) callbacks.onTerminal(parsedData as JobTerminalEvent);
                  if (callbacks.onClose) callbacks.onClose();
                  return;
                }
              } catch (parseErr) {
                // ignore malformed frame
              }
            }
          }
        }

        if (callbacks.onClose) callbacks.onClose();
      } catch (err: any) {
        if (!active) return;

        if (callbacks.onError) callbacks.onError(err);

        // Terminal auth errors should not retry
        if (err instanceof ApiError && (err.status === 401 || err.status === 403 || err.status === 404)) {
          active = false;
          return;
        }

        retryCount++;
        if (retryCount <= maxRetries) {
          if (callbacks.onReconnecting) callbacks.onReconnecting();
          const backoffDelay = Math.min(1000 * Math.pow(2, retryCount - 1), 8000);
          reconnectTimeoutId = setTimeout(startStreaming, backoffDelay);
        } else if (fallbackToPolling) {
          // Switch to polling fallback
          if (callbacks.onFallback) callbacks.onFallback();
          fallbackUnpoll = this.pollJob(
            jobId,
            (job) => {
              if (!active) return;
              if (callbacks.onEvent) {
                callbacks.onEvent({
                  job_id: job.job_id,
                  event_id: lastSeenEventId + 1,
                  to_state: job.state,
                  message: job.error || "Polled state update",
                  created_at: job.updated_at || job.created_at,
                });
              }
              const stateLower = (job.state || "").toLowerCase();
              if (["pr_created", "pr_merged", "pr_closed", "failed", "superseded", "rolled_back"].includes(stateLower)) {
                active = false;
                if (callbacks.onTerminal) {
                  callbacks.onTerminal({
                    job_id: job.job_id,
                    state: job.state,
                    error: job.error,
                    pr_number: job.pr_number,
                    pr_url: job.pr_url,
                    is_stale: job.is_stale,
                  });
                }
              }
            },
            callbacks.onError
          );
        }
      }
    };

    startStreaming();

    return () => {
      active = false;
      if (abortController) abortController.abort();
      if (reconnectTimeoutId) clearTimeout(reconnectTimeoutId);
      if (fallbackUnpoll) fallbackUnpoll();
    };
  }

  subscribeToAllEvents(callbacks: {
    onOpen?: () => void;
    onTransition?: (event: JobTransitionEvent) => void;
    onError?: (error: Error) => void;
    onClose?: () => void;
  }): () => void {
    let active = true;
    let abortController: AbortController | null = null;
    let reconnectTimeoutId: NodeJS.Timeout | null = null;
    let fallbackUnpoll: (() => void) | null = null;
    let lastSeenEventId = 0;
    let retryCount = 0;

    const startStreaming = async () => {
      if (!active) return;
      abortController = new AbortController();

      const requestHeaders: Record<string, string> = {
        Accept: "text/event-stream",
      };
      if (this.apiKey) {
        requestHeaders["Authorization"] = `Bearer ${this.apiKey}`;
      }
      if (lastSeenEventId > 0) {
        requestHeaders["Last-Event-ID"] = String(lastSeenEventId);
      }

      try {
        const url = `${this.getBaseUrl().replace(/\/$/, "")}/events`;
        const response = await fetch(url, {
          headers: requestHeaders,
          signal: abortController.signal,
        });

        if (!response.ok) {
          throw new ApiError(response.status, `SSE connection failed with status ${response.status}`);
        }

        if (!response.body) {
          throw new Error("Streaming body not available in response");
        }

        retryCount = 0;
        if (callbacks.onOpen) callbacks.onOpen();

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (active) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const frames = buffer.split("\n\n");
          buffer = frames.pop() || "";

          for (const frame of frames) {
            if (!frame.trim() || frame.startsWith(":")) continue;

            const lines = frame.split("\n");
            let eventName = "message";
            let eventId: number | null = null;
            let dataStr = "";

            for (const line of lines) {
              if (line.startsWith("event: ")) {
                eventName = line.slice(7).trim();
              } else if (line.startsWith("id: ")) {
                try {
                  eventId = parseInt(line.slice(4).trim(), 10);
                  if (!isNaN(eventId)) {
                    lastSeenEventId = Math.max(lastSeenEventId, eventId);
                  }
                } catch {
                  // ignore
                }
              } else if (line.startsWith("data: ")) {
                dataStr = line.slice(6).trim();
              }
            }

            if (dataStr) {
              try {
                const parsedData = JSON.parse(dataStr);
                if (callbacks.onTransition) {
                  callbacks.onTransition(parsedData as JobTransitionEvent);
                }
              } catch {
                // ignore
              }
            }
          }
        }

        if (callbacks.onClose) callbacks.onClose();
      } catch (err: any) {
        if (!active) return;
        if (callbacks.onError) callbacks.onError(err);

        retryCount += 1;
        if (retryCount <= 3) {
          const backoff = Math.min(1000 * Math.pow(2, retryCount - 1), 5000);
          reconnectTimeoutId = setTimeout(startStreaming, backoff);
        } else {
          // Fallback to polling
          let pollTimer: NodeJS.Timeout | null = null;
          let lastPolledIds: Record<string, string> = {};

          const pollDashboard = async () => {
            if (!active) return;
            try {
              const res = await this.getJobs({ limit: 20 });
              for (const job of res.jobs || []) {
                const prev = lastPolledIds[job.job_id];
                if (prev !== job.state) {
                  lastPolledIds[job.job_id] = job.state;
                  if (callbacks.onTransition) {
                    callbacks.onTransition({
                      job_id: job.job_id,
                      repository: job.repository,
                      event_id: 0,
                      from_state: prev || null,
                      to_state: job.state,
                      message: `State updated to ${job.state}`,
                      pr_number: job.pr_number || job.pr?.number,
                      pr_url: job.pr_url || job.pr?.url,
                    });
                  }
                }
              }
            } catch {
              // ignore polling error
            }
            if (active) {
              pollTimer = setTimeout(pollDashboard, 4000);
            }
          };

          pollDashboard();
          fallbackUnpoll = () => {
            if (pollTimer) clearTimeout(pollTimer);
          };
        }
      }
    };

    startStreaming();

    return () => {
      active = false;
      if (abortController) abortController.abort();
      if (reconnectTimeoutId) clearTimeout(reconnectTimeoutId);
      if (fallbackUnpoll) fallbackUnpoll();
    };
  }
}

export const apiClient = new PatchProofClient();
