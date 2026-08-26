from __future__ import annotations

from packages.orchestration.service import RemediationOrchestrator


def build_router(orchestrator: RemediationOrchestrator):
    from fastapi import APIRouter, HTTPException

    router = APIRouter()

    @router.post("/v1/remediations")
    def create_remediation(payload: dict):
        job_id = payload.get("job_id")
        finding = payload.get("finding")
        if not job_id or not isinstance(finding, dict):
            raise HTTPException(status_code=400, detail="job_id and finding are required")
        result = orchestrator.run(job_id, finding)
        status = 201 if result.state.value == "PR_CREATED" else 422
        return {
            "job_id": result.job_id,
            "state": result.state.value,
            "pr": result.pr,
            "evidence": result.evidence,
        }

    return router
