# GitHub integration

## Event flow

1. GitHub App sends `code_scanning_alert` webhook.
2. Webhook handler verifies `X-Hub-Signature-256`.
3. Payload is normalized into a `RemediationJob`.
4. Worker enqueues the job; the API process does not execute repository code.
5. A worker obtains an installation token and clones the repository into an isolated workspace.
6. Remediation runs through the sandbox and verification engine.
7. Only a verified result may publish a GitHub Check Run / PR.
8. Evidence is retained with the job ID and delivery ID for auditability.

## Required secrets

- `GITHUB_APP_ID`
- `GITHUB_WEBHOOK_SECRET`
- `GITHUB_PRIVATE_KEY`

Never commit any of these.

## Security rules

- Deduplicate `X-GitHub-Delivery` IDs.
- Authenticate every webhook before parsing actionable fields.
- Pin repository ref / commit SHA for remediation.
- Never execute code in the webhook HTTP process.
- Never create a PR from an unverified patch.
- Treat GitHub content as untrusted input.
