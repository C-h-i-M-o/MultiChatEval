from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RuleDictionary(Base):
    __tablename__ = "rule_dictionaries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dictionary_type: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[str] = mapped_column(String(32), default="v1")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    terms = relationship("RuleTerm", back_populates="dictionary")


class RuleTerm(Base):
    __tablename__ = "rule_terms"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dictionary_id: Mapped[int] = mapped_column(ForeignKey("rule_dictionaries.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="general")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    match_type: Mapped[str] = mapped_column(String(16), default="keyword")
    severity: Mapped[int] = mapped_column(Integer, default=1)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    dictionary = relationship("RuleDictionary", back_populates="terms")


class JudgePromptGroup(Base):
    __tablename__ = "judge_prompt_groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    rubric: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(String(32), default="v1")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    templates = relationship("JudgePromptTemplate", back_populates="group")


class JudgePromptTemplate(Base):
    __tablename__ = "judge_prompt_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("judge_prompt_groups.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    output_schema: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    group = relationship("JudgePromptGroup", back_populates="templates")
