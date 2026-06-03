"""add rule score format and safety fields

Revision ID: 20260603_01
Revises: 
Create Date: 2026-06-03
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260603_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    columns = _existing_columns("evaluation_results")
    if "format_score" not in columns:
        op.add_column(
            "evaluation_results",
            sa.Column("format_score", sa.Numeric(4, 2), nullable=False, server_default="0"),
        )
    if "safety_score" not in columns:
        op.add_column(
            "evaluation_results",
            sa.Column("safety_score", sa.Numeric(4, 2), nullable=False, server_default="0"),
        )


def downgrade() -> None:
    columns = _existing_columns("evaluation_results")
    if "safety_score" in columns:
        op.drop_column("evaluation_results", "safety_score")
    if "format_score" in columns:
        op.drop_column("evaluation_results", "format_score")


def _existing_columns(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}
