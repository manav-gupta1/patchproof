# Controlled end-to-end testing

The project now has a disposable local Git repository harness and a deterministic
end-to-end smoke test.

The smoke test intentionally does not require:

- real GitHub credentials
- paid LLM APIs
- Docker
- gVisor

Those external integrations are tested separately through adapter tests.

For staging, the same orchestration boundary can be supplied with real GitHub
App authentication, real LLM providers, Semgrep, and the gVisor sandbox.
The repository should be a dedicated non-production test repository.
