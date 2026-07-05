"""add rule dictionaries

Revision ID: 20260705_02
Revises: 20260705_01
Create Date: 2026-07-05
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260705_02"
down_revision: str | None = "20260705_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "rule_dictionaries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("dictionary_type", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("version", sa.String(length=32), server_default="v1", nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "rule_terms",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("dictionary_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=64), server_default="general", nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("match_type", sa.String(length=16), server_default="keyword", nullable=False),
        sa.Column("severity", sa.Integer(), server_default="1", nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["dictionary_id"], ["rule_dictionaries.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("rule_terms")
    op.drop_table("rule_dictionaries")
