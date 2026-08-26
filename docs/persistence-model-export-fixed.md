# Persistence model export — fixed

The canonical `JobState` is re-exported from `packages.persistence.models`
after the module's required `from __future__ import annotations` statement.
The module remains valid Python and exposes the canonical enum without
duplicating it.
