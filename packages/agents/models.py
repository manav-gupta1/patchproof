from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict

from packages.context.models import RepositoryContext
from packages.scanner.models import NormalizedFinding


class DataFlowStep(BaseModel):
    location: str
    description: str


class VulnerabilityAnalysis(BaseModel):
    finding_fingerprint: str
    classification: str
    confidence: float = Field(ge=0, le=1)
    eligible: bool
    source: str | None = None
    sink: str | None = None
    data_flow: list[DataFlowStep] = Field(default_factory=list)
    attack_hypothesis: str
    relevant_files: list[str] = Field(default_factory=list)
    reasoning: str
    limitations: list[str] = Field(default_factory=list)


class AnalystRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    finding: NormalizedFinding
    # ContextExtractor's compatibility API returns CodeContext; the canonical
    # RepositoryContext is also accepted by the production pipeline.
    context: RepositoryContext | object



class LLMProvider:
    async def complete(self, *, system: str, user: str, response_model: type[BaseModel]) -> BaseModel:
        raise NotImplementedError
