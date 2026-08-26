from __future__ import annotations

import pytest
from packages.github.installation import InstallationRegistry
from packages.jobs.store import InMemoryJobStore
from packages.webhooks.github import GitHubEvent
from packages.webhooks.handlers import WebhookDispatcher


def test_installation_created_and_deleted_lifecycle():
    registry = InstallationRegistry()
    store = InMemoryJobStore()
    dispatcher = WebhookDispatcher(jobs=store, enqueue=lambda j: None, installation_registry=registry)

    # 1. Dispatch installation.created
    event_created = GitHubEvent(
        delivery_id="deliv-inst-1",
        event="installation",
        payload={
            "action": "created",
            "installation": {
                "id": 12345,
                "account": {"login": "acme-corp", "type": "Organization"},
            },
            "repositories": [
                {"full_name": "acme-corp/service-auth"},
                {"full_name": "acme-corp/service-billing"},
            ],
        },
    )
    res_created = dispatcher.dispatch(event_created)
    assert res_created["accepted"] is True
    assert res_created["result"]["action"] == "created"

    # Verify authorization
    assert registry.is_repository_authorized(12345, "acme-corp/service-auth") is True
    assert registry.is_repository_authorized(12345, "acme-corp/service-billing") is True
    assert registry.is_repository_authorized(12345, "acme-corp/other-repo") is False

    # 2. Dispatch installation.deleted
    event_deleted = GitHubEvent(
        delivery_id="deliv-inst-2",
        event="installation",
        payload={
            "action": "deleted",
            "installation": {"id": 12345},
        },
    )
    res_deleted = dispatcher.dispatch(event_deleted)
    assert res_deleted["accepted"] is True
    assert res_deleted["result"]["action"] == "deleted"

    # All repos now de-authorized
    assert registry.is_repository_authorized(12345, "acme-corp/service-auth") is False


def test_installation_repositories_added_and_removed():
    registry = InstallationRegistry()
    registry.register_installation(
        installation_id=54321,
        account_login="fintech-inc",
        repositories=["fintech-inc/core-api"],
    )

    store = InMemoryJobStore()
    dispatcher = WebhookDispatcher(jobs=store, enqueue=lambda j: None, installation_registry=registry)

    # 1. Add repository
    event_added = GitHubEvent(
        delivery_id="deliv-inst-3",
        event="installation_repositories",
        payload={
            "action": "added",
            "installation": {"id": 54321},
            "repositories_added": [
                {"full_name": "fintech-inc/mobile-app"},
            ],
        },
    )
    res_added = dispatcher.dispatch(event_added)
    assert res_added["accepted"] is True
    assert "fintech-inc/mobile-app" in res_added["result"]["repositories_added"]

    assert registry.is_repository_authorized(54321, "fintech-inc/mobile-app") is True

    # 2. Remove repository
    event_removed = GitHubEvent(
        delivery_id="deliv-inst-4",
        event="installation_repositories",
        payload={
            "action": "removed",
            "installation": {"id": 54321},
            "repositories_removed": [
                {"full_name": "fintech-inc/core-api"},
            ],
        },
    )
    res_removed = dispatcher.dispatch(event_removed)
    assert res_removed["accepted"] is True
    assert registry.is_repository_authorized(54321, "fintech-inc/core-api") is False
    assert registry.is_repository_authorized(54321, "fintech-inc/mobile-app") is True


def test_webhook_rejects_unauthorized_installation_repository():
    registry = InstallationRegistry()
    registry.register_installation(
        installation_id=777,
        account_login="allowed-org",
        repositories=["allowed-org/monitored-repo"],
    )

    store = InMemoryJobStore()
    dispatcher = WebhookDispatcher(jobs=store, enqueue=lambda j: None, installation_registry=registry)

    # Inbound pull_request for an unauthorized repository under installation 777
    event_unauthorized = GitHubEvent(
        delivery_id="deliv-unauth-1",
        event="pull_request",
        payload={
            "action": "opened",
            "repository": {"full_name": "attacker-org/malicious-repo"},
            "pull_request": {"number": 1, "head": {"sha": "a" * 40, "ref": "feature"}},
            "installation": {"id": 777},
        },
    )
    res = dispatcher.dispatch(event_unauthorized)
    assert res["accepted"] is False
    assert res["reason"] == "repository_not_authorized_under_installation"
    assert store.count_jobs() == 0

    # Inbound pull_request for an authorized repository
    event_authorized = GitHubEvent(
        delivery_id="deliv-auth-1",
        event="pull_request",
        payload={
            "action": "opened",
            "repository": {"full_name": "allowed-org/monitored-repo"},
            "pull_request": {"number": 2, "head": {"sha": "b" * 40, "ref": "patch"}},
            "installation": {"id": 777},
        },
    )
    res_auth = dispatcher.dispatch(event_authorized)
    assert res_auth["accepted"] is True
    assert "job_id" in res_auth
    assert store.count_jobs() == 1
