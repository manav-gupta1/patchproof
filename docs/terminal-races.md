# Terminal-state race hardening

The production store is now tested at the terminal transition boundary.

Success and failure both use conditional SQL updates that require a live
lease and current ownership. Concurrent success/failure attempts therefore
have exactly one terminal winner.

The suite also verifies that an expired lease cannot publish either terminal
state and that an already-terminal job cannot be overwritten by the former
worker.

This closes the terminal-state race between success, failure, and lease
expiry.
