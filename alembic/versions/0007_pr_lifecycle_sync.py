from alembic import op
import sqlalchemy as sa

revision = "0007_pr_lifecycle_sync"
down_revision = "0006_policy_decision"
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import inspect
    conn = op.get_bind()
    insp = inspect(conn)
    cols = [c["name"] for c in insp.get_columns("jobs")]

    if "pr_number" not in cols:
        op.add_column("jobs", sa.Column("pr_number", sa.Integer(), nullable=True))
    if "pr_url" not in cols:
        op.add_column("jobs", sa.Column("pr_url", sa.String(512), nullable=True))
    if "remediation_branch" not in cols:
        op.add_column("jobs", sa.Column("remediation_branch", sa.String(256), nullable=True))
    if "current_head_sha" not in cols:
        op.add_column("jobs", sa.Column("current_head_sha", sa.String(64), nullable=True))
    if "verified_sha" not in cols:
        op.add_column("jobs", sa.Column("verified_sha", sa.String(64), nullable=True))
    if "merge_commit_sha" not in cols:
        op.add_column("jobs", sa.Column("merge_commit_sha", sa.String(64), nullable=True))
    if "is_stale" not in cols:
        op.add_column("jobs", sa.Column("is_stale", sa.Boolean(), default=False, nullable=True))
    if "invalidation_reason" not in cols:
        op.add_column("jobs", sa.Column("invalidation_reason", sa.Text(), nullable=True))
    if "invalidated_by_sha" not in cols:
        op.add_column("jobs", sa.Column("invalidated_by_sha", sa.String(64), nullable=True))


def downgrade():
    for col in [
        "invalidated_by_sha",
        "invalidation_reason",
        "is_stale",
        "merge_commit_sha",
        "verified_sha",
        "current_head_sha",
        "remediation_branch",
        "pr_url",
        "pr_number",
    ]:
        try:
            op.drop_column("jobs", col)
        except Exception:
            pass
