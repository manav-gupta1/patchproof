from packages.durable.store import DurableJobStore
from apps.worker_runtime import WorkerRuntime


class FakeQueue:
    def __init__(self):
        self.acked = []

    def read(self, consumer, count=1):
        return [("patchproof:jobs", [(b"1-0", {b"job_id": b"job-1"})])]

    def ack(self, message_id):
        self.acked.append(message_id)


def test_worker_claims_runs_and_acks():
    store = DurableJobStore()
    store.create("job-1")

    called = []
    def orchestrator(job_id):
        called.append(job_id)
        return {"state": "PR_CREATED"}

    q = FakeQueue()
    worker = WorkerRuntime(store, q, orchestrator, "worker-a")
    result = worker.run_once()

    assert called == ["job-1"]
    assert q.acked == [b"1-0"]
    assert result[0]["status"] == "processed"
