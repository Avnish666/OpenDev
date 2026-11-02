from datetime import datetime
from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Index, JSON, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class RewardTier(Base):
    __tablename__ = 'reward_tiers'
    __table_args__ = (
        CheckConstraint('price_cents > 0', name='ck_reward_price'),
        CheckConstraint('quantity_limit IS NULL OR quantity_limit > 0', name='ck_reward_quantity'),
        CheckConstraint("currency = 'USD'", name='ck_reward_currency'),
        Index('uq_reward_project_name', 'project_id', text('lower(TRIM(BOTH FROM name))'), unique=True),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    price_cents: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3), default='USD')
    benefits: Mapped[list[dict[str, str]]] = mapped_column(JSON)
    quantity_limit: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
