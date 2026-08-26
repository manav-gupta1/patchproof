
from __future__ import annotations
import threading


class LeaseLost(RuntimeError):
    pass


class _LeaseHeartbeat:
    def __init__(self, store, job_id, worker_id, lease_seconds, interval):
        self.store = store
        self.job_id = job_id
        self.worker_id = worker_id
        self.lease_seconds = lease_seconds
        self.interval = interval
        self.stop = threading.Event()
        self.lost = threading.Event()
        self.thread = None

    def start(self):
        def loop():
            while not self.stop.wait(self.interval):
                try:
                    self.store.heartbeat(
                        self.job_id, self.worker_id,
                        lease_seconds=self.lease_seconds,
                    )
                except Exception:
                    self.lost.set()
                    return
        self.thread = threading.Thread(target=loop, daemon=True)
        self.thread.start()

    def close(self):
        self.stop.set()
        if self.thread:
            self.thread.join(timeout=max(1, self.interval + 1))


class EndToEndWorker:
    """Lease-owned orchestration with heartbeat/fencing for long jobs."""

    def __init__(
        self, store, verification_service, publication_service,
        lease_seconds=60, heartbeat_interval=20,
    ):
        if heartbeat_interval >= lease_seconds:
            raise ValueError("heartbeat interval must be shorter than lease")
        self.store = store
        self.verification_service = verification_service
        self.publication_service = publication_service
        self.lease_seconds = lease_seconds
        self.heartbeat_interval = heartbeat_interval

    def run(self, *, job, patch_diff, title, body, head, base, worker_id):
        if not self.store.claim(
            job.job_id, worker_id, lease_seconds=self.lease_seconds
        ):
            return False

        hb = _LeaseHeartbeat(
            self.store, job.job_id, worker_id,
            self.lease_seconds, self.heartbeat_interval,
        )
        hb.start()
        try:
            bundle, _ = self.verification_service.verify(
                job=job, patch_diff=patch_diff
            )
            if hb.lost.is_set():
                raise LeaseLost("worker lease lost during verification")

            self.publication_service.publish(
                job=job, title=title, body=body,
                head=head, base=base,
            )
            if hb.lost.is_set():
                raise LeaseLost("worker lease lost during publication")

            self.store.succeed(job.job_id, worker_id)
            return True
        except Exception as exc:
            try:
                if not hb.lost.is_set():
                    self.store.fail(job.job_id, worker_id, str(exc))
            except Exception:
                pass
            raise
        finally:
            hb.close()
