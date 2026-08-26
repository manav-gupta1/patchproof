from __future__ import annotations

import uuid

from packages.agents.analyst import AnalystAgent
from packages.agents.metadata import ModelInvocation, now_utc
from packages.agents.models import AnalystRequest, VulnerabilityAnalysis
from packages.agents.router import ModelRouter


class AnalystService:
    def __init__(self, router: ModelRouter) -> None:
        self.router = router

    async def analyze(self, request: AnalystRequest) -> tuple[VulnerabilityAnalysis, ModelInvocation]:
        route = self.router.route("reasoning")
        request_id = str(uuid.uuid4())
        started = now_utc()

        agent = AnalystAgent(route.provider)
        result = await agent.analyze(request)

        completed = now_utc()
        invocation = ModelInvocation(
            request_id=request_id,
            route=route.name,
            provider=type(route.provider).__name__,
            model=route.model,
            started_at=started,
            completed_at=completed,
            attempts=1,
            success=True,
            response_schema=VulnerabilityAnalysis.__name__,
        )
        return result, invocation
