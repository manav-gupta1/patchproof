import threading
from datetime import datetime, timedelta, timezone


class Queue:
    def __init__(self, count):
        self.lock=threading.Lock()
        self.jobs={f"job-{i}":{"status":"queued","owner":None,"result":None}
                   for i in range(count)}

    def claim(self, worker):
        with self.lock:
            for job_id, job in self.jobs.items():
                if job["status"]=="queued":
                    job["status"]="running"
                    job["owner"]=worker
                    return job_id
        return None

    def complete(self, job_id, worker, result):
        with self.lock:
            job=self.jobs[job_id]
            if job["status"]!="running" or job["owner"]!=worker:
                return False
            job["status"]="succeeded"
            job["owner"]=None
            job["result"]=result
            return True


def test_many_workers_each_job_has_exactly_one_successful_owner():
    queue=Queue(100)
    successes=[]
    lock=threading.Lock()
    barrier=threading.Barrier(8)

    def worker(worker_id):
        barrier.wait()
        while True:
            job_id=queue.claim(worker_id)
            if job_id is None:
                return
            assert queue.complete(job_id, worker_id, {"worker":worker_id})
            with lock:
                successes.append(job_id)

    threads=[threading.Thread(target=worker,args=(f"worker-{i}",))
             for i in range(8)]
    for t in threads: t.start()
    for t in threads: t.join()

    assert len(successes)==100
    assert len(set(successes))==100
    assert all(j["status"]=="succeeded" for j in queue.jobs.values())


def test_repeated_contention_does_not_duplicate_completion():
    for _ in range(10):
        queue=Queue(25)
        completions=[]
        lock=threading.Lock()

        def worker(worker_id):
            while True:
                job_id=queue.claim(worker_id)
                if job_id is None:
                    return
                if queue.complete(job_id, worker_id, worker_id):
                    with lock:
                        completions.append(job_id)

        threads=[threading.Thread(target=worker,args=(f"w{i}",))
                 for i in range(6)]
        for t in threads: t.start()
        for t in threads: t.join()

        assert len(completions)==25
        assert len(set(completions))==25
