from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserTokenQuota(Base):
    __tablename__ = "user_token_quotas"
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_token_quotas_user"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    daily_limit: Mapped[int] = mapped_column(default=100_000)


class DailyUserTokenUsage(Base):
    __tablename__ = "daily_user_token_usage"
    __table_args__ = (
        UniqueConstraint("user_id", "usage_date", name="uq_daily_user_token_usage_user_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    usage_date: Mapped[date] = mapped_column(Date)
    total_tokens: Mapped[int] = mapped_column(default=0)


class TokenUsageLog(Base):
    __tablename__ = "token_usage_logs"
    __table_args__ = (UniqueConstraint("response_id", name="uq_token_usage_logs_response"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    task_id: Mapped[int] = mapped_column(ForeignKey("evaluation_tasks.id"))
    response_id: Mapped[int] = mapped_column(ForeignKey("model_responses.id"))
    model_config_id: Mapped[int | None] = mapped_column(ForeignKey("model_configs.id"), nullable=True)
    usage_date: Mapped[date] = mapped_column(Date)
    total_tokens: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
