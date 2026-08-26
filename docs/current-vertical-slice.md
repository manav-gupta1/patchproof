# Current vertical-slice baseline

This pass inventories the actual public interfaces in the current execution,
sandbox, verification, evidence, and publication layers and identifies tests
that already exercise multiple layers together.

No legacy API was reintroduced. The next implementation should use the
current concrete interfaces to establish one authoritative end-to-end test.
