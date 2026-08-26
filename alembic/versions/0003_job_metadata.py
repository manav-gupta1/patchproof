from alembic import op
import sqlalchemy as sa

revision = "0003_job_metadata"
down_revision = "0002_evidence_bundles"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("jobs", sa.Column("error", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("pr_data", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("evidence_data", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column("jobs", "updated_at")
    op.drop_column("jobs", "evidence_data")
    op.drop_column("jobs", "pr_data")
    op.drop_column("jobs", "error")
