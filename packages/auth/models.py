from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TenantContext:
    """Authenticated tenant identity with repository authorization scopes."""

    tenant_id: str
    name: str
    allowed_repositories: tuple[str, ...] = field(default_factory=tuple)
    is_admin: bool = False

    def can_access_repository(self, repository: str | None) -> bool:
        """Check if the tenant has permission to access the target repository."""
        if not repository:
            return False
        if self.is_admin or "*" in self.allowed_repositories:
            return True

        repo_lower = repository.strip().lower()
        for pattern in self.allowed_repositories:
            pat_lower = pattern.strip().lower()
            if pat_lower == repo_lower:
                return True
            if fnmatch.fnmatch(repo_lower, pat_lower):
                return True
        return False
