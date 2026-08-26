# Current vertical-slice gate

The current execution → sandbox → verification → evidence path is gated by
the repository's existing integration tests:

- `tests/test_verification.py`
- `tests/test_durable_verification.py`
- `tests/test_e2e_fixture.py`

This gate uses current production interfaces and does not depend on legacy
vertical-slice constructors.
