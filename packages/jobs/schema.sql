CREATE TABLE IF NOT EXISTS remediation_jobs (
    id UUID PRIMARY KEY,
    repository TEXT NOT NULL,
    commit_sha TEXT NOT NULL,
    finding_fingerprint TEXT NOT NULL,
    state TEXT NOT NULL,
    attempt INTEGER NOT NULL DEFAULT 0,
    lease_owner TEXT,
    lease_expires_at TIMESTAMPTZ,
    failure_code TEXT,
    failure_message TEXT,
    evidence_id TEXT,
    pull_request_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS job_idempotency_keys (
    idempotency_key TEXT PRIMARY KEY,
    job_id UUID NOT NULL REFERENCES remediation_jobs(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS job_events (
    id BIGSERIAL PRIMARY KEY,
    job_id UUID NOT NULL REFERENCES remediation_jobs(id),
    from_state TEXT,
    to_state TEXT NOT NULL,
    event_type TEXT NOT NULL,
    message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jobs_ready
    ON remediation_jobs (state, updated_at);

CREATE INDEX IF NOT EXISTS idx_jobs_lease
    ON remediation_jobs (lease_expires_at);

CREATE INDEX IF NOT EXISTS idx_job_events_job
    ON job_events (job_id, created_at);
