CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    repository TEXT NOT NULL,
    commit_sha TEXT NOT NULL,
    finding_fingerprint TEXT NOT NULL,
    state TEXT NOT NULL,
    version BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_jobs_state ON jobs(state);
CREATE INDEX IF NOT EXISTS idx_jobs_repo_finding ON jobs(repository, finding_fingerprint);

CREATE TABLE IF NOT EXISTS state_transitions (
    id BIGSERIAL PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    from_state TEXT NOT NULL,
    to_state TEXT NOT NULL,
    actor TEXT NOT NULL,
    reason TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_state_transitions_job ON state_transitions(job_id, occurred_at);

CREATE TABLE IF NOT EXISTS evidence (
    evidence_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    sha256 CHAR(64) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(job_id, sha256)
);

CREATE TABLE IF NOT EXISTS patches (
    patch_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    decision TEXT NOT NULL,
    changed_files JSONB NOT NULL,
    explanation TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS verification_runs (
    verification_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    baseline_reproduced BOOLEAN NOT NULL,
    patched_blocked BOOLEAN NOT NULL,
    tests_passed BOOLEAN NOT NULL,
    semgrep_clean BOOLEAN NOT NULL,
    semgrep_finding_count INTEGER NOT NULL,
    verified BOOLEAN NOT NULL,
    evidence_id TEXT REFERENCES evidence(evidence_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS pull_requests (
    pull_request_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    repository TEXT NOT NULL,
    number INTEGER,
    url TEXT,
    branch TEXT NOT NULL,
    state TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    merged_at TIMESTAMPTZ
);
