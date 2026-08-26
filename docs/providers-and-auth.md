# Provider and GitHub authentication

## GitHub App

`GitHubInstallationAuth` creates short-lived App JWTs and exchanges an
installation ID for an installation access token. The private key is supplied
through configuration; it is never stored in source code.

## LLM routing

Two provider adapters are included:

- `OpenAIProvider` for lightweight triage (default model configured as
  `gpt-5-nano`).
- `AnthropicProvider` for reasoning/patch generation (default model configured
  as `claude-sonnet-4-6`).

Provider calls are injected into `LLMRouter`, so switching models does not
change remediation orchestration.

## Patch safety

`LLMOutputGuard` requires a bounded unified Git diff before `git apply`.
The patch is still checked with `git apply --check` before application.

API keys and GitHub private keys must come from environment/secret management,
not repository files.
