import random
from datetime import datetime, timedelta, timezone


class FaultyQueue:
    def __init__(self, count, lease_seconds=1):
        self.jobs={
            f"job-{i}":{
                "status":"queued","owner":None,"lease_until":None,"result":None
            } for i in range(count)
        }
        self.lease_seconds=lease_seconds

    def claim(self, worker, now):
        for job_id, job in self.jobs.items():
            if job["status"]=="queued":
                job.update(
                    status="running",
                    owner=worker,
                    lease_until=now+timedelta(seconds=self.lease_seconds),
                )
                return job_id
        return None

    def recover(self, now):
        recovered=0
        for job in self.jobs.values():
            if job["status"]=="running" and job["lease_until"] <= now:
                job.update(status="queued", owner=None, lease_until=None)
                recovered += 1
        return recovered

    def complete(self, job_id, worker, now, result):
        job=self.jobs[job_id]
        if (
            job["status"]!="running"
            or job["owner"]!=worker
            or job["lease_until"] <= now
        ):
            return False
        job.update(status="succeeded", owner=None, lease_until=None, result=result)
        return True


def test_fault_injection_recovers_workers_that_die_after_claim():
    q=FaultyQueue(50)
    now=datetime.now(timezone.utc)
    rng=random.Random(7)
    completed=0

    for i in range(250):
        worker=f"w{i%8}"
        job=q.claim(worker,now)
        if job is None:
            now += timedelta(seconds=2)
            q.recover(now)
            job=q.claim(worker,now)
            if job is None:
                continue
        if rng.random() < 0.35:
            now += timedelta(seconds=2)
            q.recover(now)
            continue
        if q.complete(job,worker,now,{"worker":worker}):
            completed += 1

    now += timedelta(seconds=2)
    q.recover(now)

    assert completed > 0
    assert all(j["status"] in {"queued","succeeded"} for j in q.jobs.values())
    assert not any(
        j["status"]=="running" and j["lease_until"] <= now
        for j in q.jobs.values()
    )


def test_stale_worker_cannot_complete_after_fault_injected_recovery():
    q=FaultyQueue(1)
    t=datetime.now(timezone.utc)
    job=q.claim("old",t)
    assert job=="job-0"

    expired=t+timedelta(seconds=2)
    assert q.recover(expired)==1

    assert q.claim("new",expired)=="job-0"
    assert q.complete("job-0","old",expired,{"stale":True}) is False
    assert q.complete("job-0","new",expired,{"ok":True}) is True
    assert q.jobs["job-0"]["result"]=={"ok":True}


def test_fault_injection_does_not_create_duplicate_success():
    q=FaultyQueue(20)
    now=datetime.now(timezone.utc)
    rng=random.Random(19)

    for _ in range(200):
        job=q.claim("worker",now)
        if job is None:
            now += timedelta(seconds=2)
            q.recover(now)
            continue
        if rng.random() < 0.5:
            now += timedelta(seconds=2)
            q.recover(now)
        else:
            q.complete(job,"worker",now,{"ok":True})

    now += timedelta(seconds=2)
    q.recover(now)

    succeeded=sum(j["status"]=="succeeded" for j in q.jobs.values())
    assert succeeded <= 20
    assert all(
        not (j["status"]=="running" and j["lease_until"] <= now)
        for j in q.jobs.values()
    )
