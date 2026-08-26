from __future__ import annotations

from packages.state import JobState
from packages.context.extractor import ContextExtractor


class RemediationPipeline:
    """
    Orchestration boundary.

    Individual adapters (Semgrep, context builder, LLM patcher, sandbox,
    verifier, GitHub PR client) are injected so the worker never owns
    provider-specific logic.
    """

    def __init__(
        self,
        *,
        triage,
        context,
        patcher,
        applier,
        verifier,
        github,
    ):
        self.triage = triage
        self.context = context
        self.patcher = patcher
        self.applier = applier
        self.verifier = verifier
        self.github = github

    def run(self, job, repository):
        if job.state == JobState.RECEIVED:
            self.triage.run(job, repository)

        if job.state == JobState.TRIAGED:
            self.context.run(job, repository)

        if job.state == JobState.CONTEXT_BUILT:
            self.patcher.run(job, repository)

        if job.state == JobState.PATCH_GENERATED:
            self.applier.run(job, repository)

        if job.state == JobState.PATCH_APPLIED:
            self.verifier.run(job, repository)

        if job.state == JobState.VERIFIED:
            self.github.create_pr(job, repository)
