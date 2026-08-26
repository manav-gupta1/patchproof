"""initial remediation persistence

Revision ID: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None


def upgrade():
    op.create_table(
        "remediation_jobs",
        sa.Column("job_id", sa.String(128), primary_key=True),
        sa.Column("state", sa.String(64), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lease_owner", sa.String(128)),
        sa.Column("lease_until", sa.DateTime(timezone=True)),
        sa.Column("error", sa.Text()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "job_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.String(128), nullable=False),
        sa.Column("from_state", sa.String(64), nullable=False),
        sa.Column("to_state", sa.String(64), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "idempotency_keys",
        sa.Column("key", sa.String(256), primary_key=True),
        sa.Column("job_id", sa.String(128), nullable=False, unique=True),
    )


def downgrade():
    op.drop_table("idempotency_keys")
    op.drop_table("job_events")
    op.drop_table("remediation_jobs")
