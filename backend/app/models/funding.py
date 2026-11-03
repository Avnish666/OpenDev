from datetime import datetime
from sqlalchemy import BigInteger, String, ForeignKey, JSON, DateTime, UniqueConstraint, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Contribution(Base):
    __tablename__ = 'contributions'
    __table_args__ = (UniqueConstraint('user_id','checkout_key'), CheckConstraint('amount_cents > 0',name='ck_contribution_amount'), CheckConstraint('refund_total_cents IS NULL OR (refund_total_cents >= 0 AND refund_total_cents <= amount_cents)',name='ck_contribution_refund_total'))
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'), index=True)
    tier_id: Mapped[int] = mapped_column(ForeignKey('reward_tiers.id'), index=True)
    checkout_key: Mapped[str] = mapped_column(String(36))
    amount_cents: Mapped[int] = mapped_column(BigInteger)
    # NULL means no authoritative cumulative refund observation, never invented 0.
    refund_total_cents: Mapped[int | None] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3))
    reward_snapshot: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(24), default='creating')
    order_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    capture_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    approval_url: Mapped[str | None] = mapped_column(String(1000))
    capture_key: Mapped[str] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Entitlement(Base):
    __tablename__ = 'reward_entitlements'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    contribution_id: Mapped[str] = mapped_column(ForeignKey('contributions.id'), unique=True)
    status: Mapped[str] = mapped_column(String(24), default='granted')
    fulfillment_note: Mapped[str] = mapped_column(String(2000), default='')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class WebhookEvent(Base):
    __tablename__ = 'paypal_events'
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RefundRecord(Base):
    __tablename__ = 'paypal_refunds'
    __table_args__ = (
        CheckConstraint('amount_cents > 0',name='ck_refund_amount'),
        CheckConstraint('provider_total_cents IS NULL OR provider_total_cents >= amount_cents',name='ck_refund_provider_total'),
    )
    id: Mapped[str] = mapped_column(String(64),primary_key=True)
    contribution_id: Mapped[str] = mapped_column(ForeignKey('contributions.id'),index=True)
    capture_id: Mapped[str] = mapped_column(String(64))
    event_id: Mapped[str] = mapped_column(ForeignKey('paypal_events.id'))
    amount_cents: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3))
    provider_total_cents: Mapped[int | None] = mapped_column(BigInteger)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now())
