from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ModelProvider(Base):
    __tablename__ = "model_providers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    base_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    api_key_encrypted: Mapped[str | None] = mapped_column(String(512), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    models = relationship("ModelConfig", back_populates="provider")


class ModelConfig(Base):
    __tablename__ = "model_configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("model_providers.id"))
    model_name: Mapped[str] = mapped_column(String(120))
    display_name: Mapped[str] = mapped_column(String(120))
    price_input: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=0)
    price_output: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=0)
    max_tokens: Mapped[int] = mapped_column(default=4096)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    provider = relationship("ModelProvider", back_populates="models")
    responses = relationship("ModelResponse", back_populates="model_config")
