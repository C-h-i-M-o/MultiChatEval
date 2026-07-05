"""add scoring status fields

Revision ID: 20260705_01
Revises: 20260612_01
Create Date: 2026-07-05
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260705_01"
down_revision: str | None = "20260612_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "evaluation_results",
        sa.Column("score_status", sa.String(length=32), server_default="scored", nullable=False),
    )
    op.add_column(
        "evaluation_results",
        sa.Column("excluded_from_stats", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column("evaluation_results", sa.Column("judge_score_range", sa.Numeric(4, 2), nullable=True))
    op.add_column("evaluation_results", sa.Column("judge_runs_json", sa.JSON(), nullable=True))
    op.add_column("evaluation_results", sa.Column("judge_prompt_group_code", sa.String(length=64), nullable=True))
    op.add_column("evaluation_results", sa.Column("judge_prompt_version", sa.String(length=32), nullable=True))
    op.add_column("evaluation_results", sa.Column("rule_dictionary_version", sa.String(length=32), nullable=True))
    op.alter_column(
        "evaluation_results",
        "judge_score",
        existing_type=sa.Numeric(4, 2),
        nullable=True,
    )
    op.alter_column(
        "evaluation_results",
        "final_score",
        existing_type=sa.Numeric(4, 2),
        nullable=True,
    )


def downgrade() -> None:
    op.execute("UPDATE evaluation_results SET final_score = 0 WHERE final_score IS NULL")
    op.alter_column(
        "evaluation_results",
        "final_score",
        existing_type=sa.Numeric(4, 2),
        nullable=False,
    )
    op.alter_column(
        "evaluation_results",
        "judge_score",
        existing_type=sa.Numeric(4, 2),
        nullable=True,
    )
    op.drop_column("evaluation_results", "rule_dictionary_version")
    op.drop_column("evaluation_results", "judge_prompt_version")
    op.drop_column("evaluation_results", "judge_prompt_group_code")
    op.drop_column("evaluation_results", "judge_runs_json")
    op.drop_column("evaluation_results", "judge_score_range")
    op.drop_column("evaluation_results", "excluded_from_stats")
    op.drop_column("evaluation_results", "score_status")
