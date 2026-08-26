from alembic import op
import sqlalchemy as sa

revision = "0005_check_run_id"
down_revision = "0004_installation_id"
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import inspect
    conn = op.get_bind()
    insp = inspect(conn)
    cols = [c["name"] for c in insp.get_columns("jobs")]
    if "check_run_id" not in cols:
        op.add_column("jobs", sa.Column("check_run_id", sa.BigInteger(), nullable=True))


def downgrade():
    op.drop_column("jobs", "check_run_id")
