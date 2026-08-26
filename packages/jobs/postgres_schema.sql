CREATE TYPE job_state AS ENUM (
  'created','queued','cloning','scanning','analyzing','patching',
  'verifying','failed','verified','pr_created'
);

CREATE TABLE remediation_jobs (
  job_id UUID PRIMARY KEY,
  repository TEXT NOT NULL,
  delivery_id TEXT NOT NULL UNIQUE,
  commit_sha CHAR(40) NOT NULL,
  state job_state NOT NULL,
  attempt INTEGER NOT NULL DEFAULT 0,
  error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE job_events (
  id BIGSERIAL PRIMARY KEY,
  job_id UUID NOT NULL REFERENCES remediation_jobs(job_id) ON DELETE CASCADE,
  from_state job_state,
  to_state job_state NOT NULL,
  message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX remediation_jobs_state_idx ON remediation_jobs(state);
CREATE INDEX job_events_job_id_idx ON job_events(job_id);
