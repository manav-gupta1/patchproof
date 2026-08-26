# Worker/SQL reconciliation

The SQL repository now explicitly maps the canonical `RemediationJob` fields
to the `JobRow` schema instead of passing the entire Pydantic model dump into
SQLAlchemy. This prevents orchestration-only fields such as failure codes and
evidence IDs from leaking into the SQL row constructor.
