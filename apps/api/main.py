from __future__ import annotations
import hashlib, json, os
from dataclasses import dataclass
from fastapi import FastAPI, Header, HTTPException, Request
from packages.github.app import GitHubAppConfig, GitHubWebhookHandler
from packages.orchestration.models import JobState, RemediationJob

app = FastAPI(title="PatchProof API", version="0.1.0")

class InMemoryJobs:
    def __init__(self): self._items = {}
    def put(self, job): self._items[job.id] = job
    def get(self, job_id): return self._items.get(job_id)

@dataclass(frozen=True)
class QueueTask:
    job_id: str
    path: str

class TestableQueue:
    def __init__(self): self._items = []
    def enqueue(self, task): self._items.append(task)
    def dequeue(self): return self._items.pop(0) if self._items else None

jobs = InMemoryJobs()
queue = TestableQueue()
webhook_secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "development-secret")
webhook = GitHubWebhookHandler(
    GitHubAppConfig(app_id="development", webhook_secret=webhook_secret)
)

@app.get("/health")
def health(): return {"status": "ok"}

@app.get("/healthz")
def healthz(): return {"status": "ok"}

@app.get("/readyz")
def readyz(): return {"status": "ready"}

@app.post("/webhooks/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str = Header(default=""),
    x_github_event: str = Header(default=""),
    x_github_delivery: str = Header(default=""),
):
    body = await request.body()
    try:
        payload = webhook.parse(body, {
            "x-hub-signature-256": x_hub_signature_256,
            "x-github-event": x_github_event,
            "x-github-delivery": x_github_delivery,
        })
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if payload is None: return {"jobs": []}

    finding = payload.finding
    fingerprint = finding.get("fingerprint") or hashlib.sha256(
        json.dumps(finding, sort_keys=True).encode()
    ).hexdigest()
    job_id = hashlib.sha256(
        f"{payload.repository}:{finding.get('alert_number')}:{fingerprint}".encode()
    ).hexdigest()[:24]
    job = RemediationJob(
        id=job_id, state=JobState.RECEIVED, repository=payload.repository,
        commit_sha=json.loads(body).get("commit_sha") or finding.get("head_sha") or "",
        finding_fingerprint=fingerprint,
    )
    jobs.put(job)
    queue.enqueue(QueueTask(job_id=job_id, path=finding.get("path") or ""))
    return {"jobs": [job_id]}
