"""add anonymous user feedback toggle

Revision ID: 20260605_01
Revises: 20260603_01
Create Date: 2026-06-05
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260605_01"
down_revision: str | None = "20260603_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("SET SESSION sql_mode = CONCAT_WS(',', @@SESSION.sql_mode, 'NO_AUTO_VALUE_ON_ZERO')")
    op.execute(
        """
        INSERT INTO users (id, username, password_hash)
        VALUES (0, 'anonymous', 'anonymous')
        ON DUPLICATE KEY UPDATE
          username = VALUES(username),
          password_hash = VALUES(password_hash)
        """
    )
    op.execute("ALTER TABLE users AUTO_INCREMENT = 1")

    if "uq_user_feedback_user_response" not in _unique_constraints("user_feedback"):
        op.create_unique_constraint(
            "uq_user_feedback_user_response",
            "user_feedback",
            ["user_id", "response_id"],
        )


def downgrade() -> None:
    if "uq_user_feedback_user_response" in _unique_constraints("user_feedback"):
        op.drop_constraint("uq_user_feedback_user_response", "user_feedback", type_="unique")


def _unique_constraints(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {constraint["name"] for constraint in inspector.get_unique_constraints(table_name)}
