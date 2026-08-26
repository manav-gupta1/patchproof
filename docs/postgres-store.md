# PostgreSQL job store

The durable SQL-backed store is now production-migration based.

## Schema

- `jobs`: one durable remediation job per GitHub delivery ID.
- `job_events`: append-only state-transition/audit records.

## Migrations

Production startup calls Alembic `upgrade head`. The initial migration creates
both tables and the unique delivery/job identifiers.

`create_all()` remains available to lightweight unit fixtures but is not the
production schema deployment mechanism.

## Webhook wiring

`packages.api.bootstrap.build_app()`:

1. applies database migrations;
2. constructs `PostgresJobStore`;
3. wires it into `WebhookDispatcher`;
4. sends accepted jobs to the registered Celery task.

This removes the in-memory job store from the real API path.
