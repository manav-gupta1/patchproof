from alembic import op
import sqlalchemy as sa

revision = "0002_evidence_bundles"
down_revision = "0001_jobs_events"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "evidence_bundles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.String(length=128), nullable=False),
        sa.Column("commit_sha", sa.String(length=40), nullable=False),
        sa.Column("patch_sha256", sa.String(length=64), nullable=False),
        sa.Column("scanner_summary", sa.Text(), nullable=False),
        sa.Column("test_summary", sa.Text(), nullable=False),
        sa.Column("verification_summary", sa.Text(), nullable=False),
        sa.Column("evidence_sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("job_id"),
        sa.UniqueConstraint("evidence_sha256"),
    )
    op.create_index(
        "ix_evidence_bundles_job_id", "evidence_bundles", ["job_id"]
    )


def downgrade():
    op.drop_index("ix_evidence_bundles_job_id", table_name="evidence_bundles")
    op.drop_table("evidence_bundles")
