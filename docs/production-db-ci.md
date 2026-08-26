# Production database CI

The production database race/integration layer is now environment
configurable.

CI reads `PATCHPROOF_DATABASE_URL`. When it is absent, production-database
tests are skipped rather than fabricating a database or silently testing a
different engine.

When configured, CI initializes the real `SQLJobStore` against that URL
and verifies schema creation plus a transaction-boundary read.

The existing local suite remains independent and continues to run without
production credentials.
