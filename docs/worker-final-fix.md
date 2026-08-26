# Worker verification-plan fix

The worker was constructing the verification plan with the retired scalar
`semgrep_config` field. It now supplies the canonical `semgrep_command`
argv, matching the current `VerificationPlan` model and sandbox execution
contract.
