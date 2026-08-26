from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class InstallationRecord:
    installation_id: int
    account_login: str
    account_type: str = "Organization"
    status: str = "active"  # "active", "suspended", "deleted"
    repositories: set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class InstallationRegistry:
    """Thread-safe registry managing GitHub App installations and repository permissions."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # Maps installation_id -> InstallationRecord
        self._installations: dict[int, InstallationRecord] = {}
        # Maps repository (lowercase "owner/repo") -> installation_id
        self._repo_to_installation: dict[str, int] = {}

    def register_installation(
        self,
        installation_id: int,
        account_login: str,
        account_type: str = "Organization",
        repositories: list[str] | set[str] | None = None,
        status: str = "active",
    ) -> InstallationRecord:
        with self._lock:
            now = datetime.now(timezone.utc)
            repo_set = {r.strip().lower() for r in (repositories or []) if r and r.strip()}
            record = InstallationRecord(
                installation_id=installation_id,
                account_login=account_login,
                account_type=account_type,
                status=status,
                repositories=repo_set,
                created_at=now,
                updated_at=now,
            )
            self._installations[installation_id] = record
            if status == "active":
                for r in repo_set:
                    self._repo_to_installation[r] = installation_id
            return record

    def get_installation(self, installation_id: int) -> InstallationRecord | None:
        with self._lock:
            return self._installations.get(installation_id)

    def is_repository_authorized(self, installation_id: int | None, repository: str) -> bool:
        """Check if target repository is actively authorized under the GitHub App installation."""
        if not repository:
            return False
        repo_lower = repository.strip().lower()
        with self._lock:
            if installation_id is not None:
                record = self._installations.get(installation_id)
                if not record or record.status != "active":
                    return False
                return repo_lower in record.repositories or "*" in record.repositories

            # If installation_id is omitted, check if repo is registered under any active installation
            mapped_inst_id = self._repo_to_installation.get(repo_lower)
            if mapped_inst_id is not None:
                record = self._installations.get(mapped_inst_id)
                return bool(record and record.status == "active")
            return False

    def handle_installation_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Handle GitHub 'installation' webhook (created, deleted, suspend, unsuspend)."""
        action = payload.get("action", "")
        installation = payload.get("installation", {})
        inst_id = installation.get("id")
        account = installation.get("account", {})
        account_login = account.get("login", "unknown")
        account_type = account.get("type", "Organization")

        if not inst_id:
            return {"handled": False, "reason": "missing_installation_id"}

        with self._lock:
            now = datetime.now(timezone.utc)
            if action == "created":
                repos = payload.get("repositories", [])
                repo_names = {r.get("full_name", "").strip().lower() for r in repos if isinstance(r, dict) and r.get("full_name")}
                record = InstallationRecord(
                    installation_id=inst_id,
                    account_login=account_login,
                    account_type=account_type,
                    status="active",
                    repositories=repo_names,
                    created_at=now,
                    updated_at=now,
                )
                self._installations[inst_id] = record
                for r in repo_names:
                    self._repo_to_installation[r] = inst_id
                return {"handled": True, "action": "created", "installation_id": inst_id, "repositories": list(repo_names)}

            elif action == "deleted":
                record = self._installations.get(inst_id)
                if record:
                    record.status = "deleted"
                    record.updated_at = now
                    for r in record.repositories:
                        if self._repo_to_installation.get(r) == inst_id:
                            self._repo_to_installation.pop(r, None)
                return {"handled": True, "action": "deleted", "installation_id": inst_id}

            elif action == "suspend":
                record = self._installations.get(inst_id)
                if record:
                    record.status = "suspended"
                    record.updated_at = now
                    for r in record.repositories:
                        if self._repo_to_installation.get(r) == inst_id:
                            self._repo_to_installation.pop(r, None)
                return {"handled": True, "action": "suspended", "installation_id": inst_id}

            elif action == "unsuspend":
                record = self._installations.get(inst_id)
                if record:
                    record.status = "active"
                    record.updated_at = now
                    for r in record.repositories:
                        self._repo_to_installation[r] = inst_id
                return {"handled": True, "action": "unsuspended", "installation_id": inst_id}

            return {"handled": False, "reason": f"unhandled_action_{action}"}

    def handle_installation_repositories_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Handle GitHub 'installation_repositories' webhook (added, removed)."""
        action = payload.get("action", "")
        installation = payload.get("installation", {})
        inst_id = installation.get("id")

        if not inst_id:
            return {"handled": False, "reason": "missing_installation_id"}

        with self._lock:
            now = datetime.now(timezone.utc)
            record = self._installations.setdefault(
                inst_id,
                InstallationRecord(
                    installation_id=inst_id,
                    account_login=installation.get("account", {}).get("login", "unknown"),
                    account_type=installation.get("account", {}).get("type", "Organization"),
                    status="active",
                    repositories=set(),
                    created_at=now,
                    updated_at=now,
                ),
            )
            record.updated_at = now

            if action == "added":
                added_repos = payload.get("repositories_added", [])
                added_names = {r.get("full_name", "").strip().lower() for r in added_repos if isinstance(r, dict) and r.get("full_name")}
                record.repositories.update(added_names)
                if record.status == "active":
                    for r in added_names:
                        self._repo_to_installation[r] = inst_id
                return {"handled": True, "action": "added", "installation_id": inst_id, "repositories_added": list(added_names)}

            elif action == "removed":
                removed_repos = payload.get("repositories_removed", [])
                removed_names = {r.get("full_name", "").strip().lower() for r in removed_repos if isinstance(r, dict) and r.get("full_name")}
                record.repositories.difference_update(removed_names)
                for r in removed_names:
                    if self._repo_to_installation.get(r) == inst_id:
                        self._repo_to_installation.pop(r, None)
                return {"handled": True, "action": "removed", "installation_id": inst_id, "repositories_removed": list(removed_names)}

            return {"handled": False, "reason": f"unhandled_action_{action}"}
