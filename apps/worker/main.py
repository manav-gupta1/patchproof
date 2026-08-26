from __future__ import annotations

import asyncio
import os

from packages.orchestration.remediation import (
    InMemoryEvidenceSink,
    RemediationOrchestrator,
)
from packages.patching import DeterministicPatchModel, PatchCandidate, PatchDecision, PatchEngine
from packages.persistence.memory import MemoryJobRepository
from packages.queue.memory import MemoryQueue
from packages.worker import Worker
from packages.verification import VerificationRunner


async def main() -> None:
    # Development worker wiring. Production replaces these with PostgreSQL,
    # Redis/Celery, a real LLM provider, and the isolated sandbox runner.
    jobs = MemoryJobRepository()
    queue = MemoryQueue()

    # Deliberately fail closed until a real model provider is configured.
    candidate = PatchCandidate(
        decision=PatchDecision.NO_PATCH,
        explanation="Development worker has no real LLM configured.",
        files={},
        changed_files=[],
        model_provider="development",
        model_name="none",
        patch_id="development-no-patch",
    )

    orchestrator = RemediationOrchestrator(
        patch_engine=PatchEngine(DeterministicPatchModel(candidate)),
        verification_runner=VerificationRunner(),
        state_store=jobs,
        evidence_sink=InMemoryEvidenceSink(),
    )

    worker = Worker(queue=queue, jobs=jobs, orchestrator=orchestrator)

    while True:
        processed = await worker.process_one(workspace=os.environ.get("WORKSPACE", "/tmp/patchproof"))
        if not processed:
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
