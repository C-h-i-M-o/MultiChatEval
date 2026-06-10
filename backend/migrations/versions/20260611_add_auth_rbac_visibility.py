"""add auth rbac and task visibility

Revision ID: 20260611_01
Revises: 20260606_01
Create Date: 2026-06-11
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260611_01"
down_revision: str | None = "20260606_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=16), server_default="user", nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("status", sa.String(length=16), server_default="active", nullable=False),
    )
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(), nullable=True))
    op.add_column(
        "evaluation_tasks",
        sa.Column("visibility", sa.String(length=16), server_default="public", nullable=False),
    )

    op.execute("UPDATE users SET status = 'disabled' WHERE id = 0")
    op.execute("UPDATE evaluation_tasks SET user_id = 0 WHERE user_id IS NULL")
    op.execute("UPDATE conversations SET user_id = 0 WHERE user_id IS NULL")
    op.execute("UPDATE user_feedback SET user_id = 0 WHERE user_id IS NULL")
    op.alter_column(
        "evaluation_tasks",
        "user_id",
        existing_type=sa.BigInteger(),
        nullable=False,
    )
    op.alter_column(
        "user_feedback",
        "user_id",
        existing_type=sa.BigInteger(),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "user_feedback",
        "user_id",
        existing_type=sa.BigInteger(),
        nullable=True,
    )
    op.alter_column(
        "evaluation_tasks",
        "user_id",
        existing_type=sa.BigInteger(),
        nullable=True,
    )
    op.drop_column("evaluation_tasks", "visibility")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "status")
    op.drop_column("users", "role")
