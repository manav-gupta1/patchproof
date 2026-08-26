from alembic import op
import sqlalchemy as sa

revision = "0008_repository_policies"
down_revision = "0007_pr_lifecycle_sync"
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import inspect
    conn = op.get_bind()
    insp = inspect(conn)
    tables = insp.get_table_names()

    if "repository_policies" not in tables:
        op.create_table(
            "repository_policies",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("repository", sa.String(512), nullable=False, unique=True, index=True),
            sa.Column("policy_data", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade():
    op.drop_table("repository_policies")
