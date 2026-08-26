from alembic import op
import sqlalchemy as sa

revision = "0001_jobs_events"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.String(length=128), nullable=False),
        sa.Column("delivery_id", sa.String(length=256), nullable=False),
        sa.Column("repository", sa.String(length=512), nullable=False),
        sa.Column("commit_sha", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("state", sa.String(length=64), nullable=False, server_default="queued"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("job_id"),
        sa.UniqueConstraint("delivery_id"),
    )
    op.create_index("ix_jobs_job_id", "jobs", ["job_id"])
    op.create_index("ix_jobs_delivery_id", "jobs", ["delivery_id"])

    op.create_table(
        "job_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.String(length=128), nullable=False),
        sa.Column("from_state", sa.String(length=64), nullable=True),
        sa.Column("to_state", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_job_events_job_id", "job_events", ["job_id"])


def downgrade():
    op.drop_index("ix_job_events_job_id", table_name="job_events")
    op.drop_table("job_events")
    op.drop_index("ix_jobs_delivery_id", table_name="jobs")
    op.drop_index("ix_jobs_job_id", table_name="jobs")
    op.drop_table("jobs")
