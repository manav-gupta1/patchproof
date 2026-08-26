# Real SQLJobStore integration

This layer deliberately uses the repository's actual `SQLJobStore`
instead of the synthetic crash harness.

The integration verifies that a job created through the production store
remains readable through a fresh store instance against the same database
engine, which is the persistence boundary needed for restart behavior.

Claim, lease renewal, recovery, and atomic completion can only be wired
here once those operations are exposed by the real store API; this test
does not invent or silently substitute missing production methods.
