"""add model billing and token quotas

Revision ID: 20260612_01
Revises: 20260611_01
Create Date: 2026-06-12
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260612_01"
down_revision: str | None = "20260611_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "model_configs",
        sa.Column("temperature", sa.Numeric(4, 2), server_default="0.70", nullable=False),
    )
    op.add_column(
        "model_configs",
        sa.Column("timeout_seconds", sa.Integer(), server_default="60", nullable=False),
    )
    op.add_column("model_configs", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column(
        "model_configs",
        sa.Column("currency", sa.String(length=3), server_default="CNY", nullable=False),
    )
    op.add_column(
        "model_configs",
        sa.Column("price_cache_hit", sa.Numeric(16, 6), server_default="0", nullable=False),
    )
    op.add_column(
        "model_configs",
        sa.Column("price_cache_creation", sa.Numeric(16, 6), server_default="0", nullable=False),
    )
    op.alter_column(
        "model_configs",
        "price_input",
        existing_type=sa.Numeric(10, 6),
        type_=sa.Numeric(16, 6),
        existing_nullable=False,
    )
    op.alter_column(
        "model_configs",
        "price_output",
        existing_type=sa.Numeric(10, 6),
        type_=sa.Numeric(16, 6),
        existing_nullable=False,
    )

    op.add_column(
        "model_responses",
        sa.Column("cache_hit_tokens", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "model_responses",
        sa.Column("cache_creation_tokens", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "model_responses",
        sa.Column("total_tokens", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "model_responses",
        sa.Column("input_cost", sa.Numeric(18, 10), server_default="0", nullable=False),
    )
    op.add_column(
        "model_responses",
        sa.Column("output_cost", sa.Numeric(18, 10), server_default="0", nullable=False),
    )
    op.add_column(
        "model_responses",
        sa.Column("cache_hit_cost", sa.Numeric(18, 10), server_default="0", nullable=False),
    )
    op.add_column(
        "model_responses",
        sa.Column("cache_creation_cost", sa.Numeric(18, 10), server_default="0", nullable=False),
    )
    op.add_column(
        "model_responses",
        sa.Column("currency", sa.String(length=3), server_default="CNY", nullable=False),
    )
    op.add_column("model_responses", sa.Column("config_snapshot", sa.JSON(), nullable=True))
    op.execute("UPDATE model_responses SET total_tokens = input_tokens + output_tokens")
    op.execute(
        """
        UPDATE model_responses AS response
        JOIN model_configs AS config ON config.id = response.model_config_id
        JOIN model_providers AS provider ON provider.id = config.provider_id
        SET response.config_snapshot = JSON_OBJECT(
            'providerName', provider.name,
            'displayName', config.display_name,
            'modelName', config.model_name,
            'baseUrl', provider.base_url,
            'maxTokens', config.max_tokens,
            'temperature', config.temperature,
            'timeoutSeconds', config.timeout_seconds,
            'currency', config.currency,
            'priceInput', config.price_input,
            'priceOutput', config.price_output,
            'priceCacheHit', config.price_cache_hit,
            'priceCacheCreation', config.price_cache_creation
        )
        WHERE response.config_snapshot IS NULL
        """
    )
    op.drop_constraint("fk_model_responses_model_config", "model_responses", type_="foreignkey")
    op.create_foreign_key(
        "fk_model_responses_model_config",
        "model_responses",
        "model_configs",
        ["model_config_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.alter_column(
        "model_responses",
        "estimated_cost",
        existing_type=sa.Numeric(10, 6),
        type_=sa.Numeric(18, 10),
        existing_nullable=False,
    )

    op.create_table(
        "user_token_quotas",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("daily_limit", sa.Integer(), server_default="100000", nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_user_token_quotas_user"),
    )
    op.create_table(
        "daily_user_token_usage",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("usage_date", sa.Date(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "usage_date", name="uq_daily_user_token_usage_user_date"),
    )
    op.create_table(
        "token_usage_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("task_id", sa.BigInteger(), nullable=False),
        sa.Column("response_id", sa.BigInteger(), nullable=False),
        sa.Column("model_config_id", sa.BigInteger(), nullable=True),
        sa.Column("usage_date", sa.Date(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["model_config_id"], ["model_configs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["response_id"], ["model_responses.id"]),
        sa.ForeignKeyConstraint(["task_id"], ["evaluation_tasks.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("response_id", name="uq_token_usage_logs_response"),
    )


def downgrade() -> None:
    op.drop_table("token_usage_logs")
    op.drop_table("daily_user_token_usage")
    op.drop_table("user_token_quotas")
    op.drop_constraint("fk_model_responses_model_config", "model_responses", type_="foreignkey")
    op.create_foreign_key(
        "fk_model_responses_model_config",
        "model_responses",
        "model_configs",
        ["model_config_id"],
        ["id"],
    )
    op.alter_column(
        "model_responses",
        "estimated_cost",
        existing_type=sa.Numeric(18, 10),
        type_=sa.Numeric(10, 6),
        existing_nullable=False,
    )
    op.drop_column("model_responses", "config_snapshot")
    op.drop_column("model_responses", "currency")
    op.drop_column("model_responses", "cache_creation_cost")
    op.drop_column("model_responses", "cache_hit_cost")
    op.drop_column("model_responses", "output_cost")
    op.drop_column("model_responses", "input_cost")
    op.drop_column("model_responses", "total_tokens")
    op.drop_column("model_responses", "cache_creation_tokens")
    op.drop_column("model_responses", "cache_hit_tokens")
    op.alter_column(
        "model_configs",
        "price_output",
        existing_type=sa.Numeric(16, 6),
        type_=sa.Numeric(10, 6),
        existing_nullable=False,
    )
    op.alter_column(
        "model_configs",
        "price_input",
        existing_type=sa.Numeric(16, 6),
        type_=sa.Numeric(10, 6),
        existing_nullable=False,
    )
    op.drop_column("model_configs", "price_cache_creation")
    op.drop_column("model_configs", "price_cache_hit")
    op.drop_column("model_configs", "currency")
    op.drop_column("model_configs", "notes")
    op.drop_column("model_configs", "timeout_seconds")
    op.drop_column("model_configs", "temperature")
