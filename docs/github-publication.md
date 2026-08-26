# Verified GitHub publication

The GitHub publisher is now a fail-closed boundary.

A pull request can only be created when:

1. verification explicitly reports `verified=True`;
2. evidence targets the exact remediation commit SHA;
3. the job is currently in the durable `verified` state;
4. the patch digest matches the evidence;
5. test and scanner summaries are present.

The PR body includes the commit SHA, patch SHA-256, test result, and scanner
result so reviewers have a compact verification record.

The publisher does not advance the state machine itself; the orchestrator must
transition `verified -> pr_created` only after publication succeeds.
