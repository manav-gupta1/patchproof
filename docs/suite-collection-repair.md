# Suite collection repair

This pass inventories the test tree and performs collection-only analysis.
It does not add fake production symbols or alter tests merely to force
collection to succeed.

Missing imports are recorded from pytest's actual collection output so the
next implementation pass can address real API/test-snapshot mismatches.
