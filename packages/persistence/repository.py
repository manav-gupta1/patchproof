from __future__ import annotations
import json
from packages.state import Job, JobState, JobStateMachine
from packages.state.evidence import make_evidence

class JobRepository:
    def __init__(self, db):
        self.db=db

    def create_job(self, job):
        with self.db.connection() as conn:
            conn.execute(
                "INSERT INTO jobs (job_id,repository,commit_sha,finding_fingerprint,state) VALUES (%s,%s,%s,%s,%s)",
                (job.job_id,job.repository,job.commit_sha,job.finding_fingerprint,job.state.value),
            )

    def get_job(self, job_id):
        with self.db.connection() as conn:
            row=conn.execute(
                "SELECT job_id,repository,commit_sha,finding_fingerprint,state FROM jobs WHERE job_id=%s",
                (job_id,),
            ).fetchone()
        if row is None: return None
        return Job(job_id=row[0],repository=row[1],commit_sha=row[2],
                   finding_fingerprint=row[3],state=JobState(row[4]))

    def transition(self, job, *, to_state, actor, reason):
        with self.db.connection() as conn:
            with conn.transaction():
                row=conn.execute(
                    "SELECT state,version FROM jobs WHERE job_id=%s FOR UPDATE",(job.job_id,)
                ).fetchone()
                if row is None: raise KeyError(job.job_id)
                current=JobState(row[0]); version=row[1]
                shadow=Job(job_id=job.job_id,repository=job.repository,commit_sha=job.commit_sha,
                           finding_fingerprint=job.finding_fingerprint,state=current)
                JobStateMachine(shadow).transition(to_state,actor=actor,reason=reason)
                updated=conn.execute(
                    "UPDATE jobs SET state=%s,version=version+1,updated_at=now() WHERE job_id=%s AND version=%s",
                    (to_state.value,job.job_id,version),
                )
                if updated.rowcount != 1: raise RuntimeError("optimistic concurrency conflict")
                conn.execute(
                    "INSERT INTO state_transitions (job_id,from_state,to_state,actor,reason) VALUES (%s,%s,%s,%s,%s)",
                    (job.job_id,current.value,to_state.value,actor,reason),
                )
                job.state=to_state

    def add_evidence(self, job_id, kind, payload):
        evidence=make_evidence(kind,payload)
        with self.db.connection() as conn:
            conn.execute(
                "INSERT INTO evidence (evidence_id,job_id,kind,sha256,payload) VALUES (%s,%s,%s,%s,%s::jsonb) ON CONFLICT (evidence_id) DO NOTHING",
                (evidence.evidence_id,job_id,evidence.kind,evidence.sha256,json.dumps(evidence.payload,default=str)),
            )
        return evidence.evidence_id
