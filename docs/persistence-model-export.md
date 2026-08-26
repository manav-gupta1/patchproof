# Persistence model export

`JobState` remains defined canonically in `packages.state.models`. The
persistence models module now re-exports that same enum so current callers
using `packages.persistence.models.JobState` resolve to the canonical type.
