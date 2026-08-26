from __future__ import annotations
import os

from packages.store.postgres import PostgresJobStore
from packages.store.bootstrap import migrate_database
from packages.jobs.celery_app import remediation_task
from packages.webhooks.handlers import WebhookDispatcher
from packages.github.installation import InstallationRegistry
from packages.config.guard import validate_production_configuration
from packages.api.app import create_app


def build_app():
    # 1. Enforce production configuration guard in production mode
    config_validation = validate_production_configuration()
    config_validation.enforce()

    # 2. Apply database migrations
    migrate_database()
    store = PostgresJobStore(os.environ["PATCHPROOF_DATABASE_URL"])

    # 3. Initialize GitHub App client & installation registry
    installation_registry = InstallationRegistry()
    check_runs = None
    try:
        from packages.github.auth import GitHubAppCredentials, GitHubAppAuth
        from packages.github.client import GitHubAppClient
        from packages.github.check_runs import GitHubCheckRunReporter
        creds = GitHubAppCredentials.from_env()
        if creds.app_id and creds.private_key_pem:
            auth = GitHubAppAuth(
                app_id=creds.app_id,
                private_key_pem=creds.private_key_pem,
                api_url=creds.api_url,
            )
            client = GitHubAppClient(auth=auth)
            check_runs = GitHubCheckRunReporter(client=client)
    except Exception:
        check_runs = None

    dispatcher = WebhookDispatcher(
        jobs=store,
        enqueue=remediation_task.delay,
        check_runs=check_runs,
        installation_registry=installation_registry,
    )
    return create_app(dispatcher=dispatcher, store=store)
