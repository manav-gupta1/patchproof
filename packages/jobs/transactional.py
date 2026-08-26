from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.store.postgres import JobModel, JobEventModel
from packages.jobs.state import JobState, JobStateMachine


class DurableJobState:
    def __init__(self, engine, machine=None):
        self.engine = engine
        self.machine = machine or JobStateMachine()

    def transition(self, job_id, target, message=""):
        with Session(self.engine) as session:
            job = session.scalar(
                select(JobModel).where(JobModel.job_id == job_id).with_for_update()
            )
            if not job:
                raise KeyError(job_id)

            current = JobState(job.state)
            target = JobState(target)
            self.machine.transition(current, target)

            job.state = target.value
            session.add(JobEventModel(
                job_id=job_id,
                from_state=current.value,
                to_state=target.value,
                message=message,
            ))
            session.commit()
            return target

    def state(self, job_id):
        with Session(self.engine) as session:
            job = session.scalar(select(JobModel).where(JobModel.job_id == job_id))
            return None if job is None else JobState(job.state)
