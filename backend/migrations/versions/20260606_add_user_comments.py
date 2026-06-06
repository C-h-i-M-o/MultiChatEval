"""add user comments

Revision ID: 20260606_01
Revises: 20260605_01
Create Date: 2026-06-06
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260606_01"
down_revision: str | None = "20260605_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_comments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("response_id", sa.BigInteger(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["response_id"], ["model_responses.id"], name="fk_user_comments_response"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_user_comments_user"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        """
        INSERT INTO user_comments (user_id, response_id, content, created_at)
        SELECT COALESCE(user_id, 0), response_id, TRIM(comment), created_at
        FROM user_feedback
        WHERE comment IS NOT NULL AND TRIM(comment) <> ''
        """
    )
    op.drop_column("user_feedback", "comment")


def downgrade() -> None:
    op.add_column("user_feedback", sa.Column("comment", sa.Text(), nullable=True))
    op.execute(
        """
        UPDATE user_feedback AS feedback
        JOIN (
          SELECT comments.user_id, comments.response_id, comments.content
          FROM user_comments AS comments
          JOIN (
            SELECT user_id, response_id, MAX(id) AS latest_id
            FROM user_comments
            GROUP BY user_id, response_id
          ) AS latest ON latest.latest_id = comments.id
        ) AS migrated
          ON migrated.user_id = feedback.user_id
         AND migrated.response_id = feedback.response_id
        SET feedback.comment = migrated.content
        """
    )
    op.drop_table("user_comments")
