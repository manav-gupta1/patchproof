from alembic import op
import sqlalchemy as sa

revision = "0004_installation_id"
down_revision = "0003_job_metadata"
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import inspect
    conn = op.get_bind()
    insp = inspect(conn)
    cols = [c["name"] for c in insp.get_columns("jobs")]
    if "installation_id" not in cols:
        op.add_column("jobs", sa.Column("installation_id", sa.Integer(), nullable=True))


def downgrade():
    op.drop_column("jobs", "installation_id")
