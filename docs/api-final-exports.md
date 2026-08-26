# API export cleanup

Corrected package exports to point at the actual implementation modules:
CommandResult, ExecutionRequest, SandboxExecutor, VerificationRunner,
ContextExtractor, RepositoryContext, PatchEngine, PatchProposal, and
VerificationPlan.

No placeholder implementation was added for symbols that have no production
definition.
