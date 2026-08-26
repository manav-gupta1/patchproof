# Reliability gate

The repository contains historical test snapshots whose imports no longer
match the current package surface. They are not used to claim a green
production suite.

This gate runs the tests that directly exercise the current SQL job/lease
implementation, including claim fencing, heartbeat fencing, terminal races,
persistence, recovery, and the real-store E2E path.

Production database integration remains opt-in through
`PATCHPROOF_DATABASE_URL`.
