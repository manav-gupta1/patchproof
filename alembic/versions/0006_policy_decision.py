from alembic import op
import sqlalchemy as sa

revision = "0006_policy_decision"
down_revision = "0005_check_run_id"
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import inspect
    conn = op.get_bind()
    insp = inspect(conn)
    cols = [c["name"] for c in insp.get_columns("jobs")]
    if "policy_data" not in cols:
        op.add_column("jobs", sa.Column("policy_data", sa.Text(), nullable=True))
    if "target_branch" not in cols:
        op.add_column("jobs", sa.Column("target_branch", sa.String(256), nullable=True))


def downgrade():
    op.drop_column("jobs", "target_branch")
    op.drop_column("jobs", "policy_data")
