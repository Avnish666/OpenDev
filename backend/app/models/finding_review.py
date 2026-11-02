"""Append-only human opinions; not ledger corrections or payment certification."""
from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class FindingReview(Base):
    __tablename__ = 'finding_reviews'
    __table_args__ = (
        UniqueConstraint('actor_id','request_key',name='uq_review_actor_request'),
        CheckConstraint("action IN ('explain','accept_field','dispute_field','mark_reviewed','request_retry')",name='ck_review_action'),
        CheckConstraint('length(trim(reason)) >= 10',name='ck_review_reason'),
        Index('ix_reviews_extraction_finding_created','extraction_id','finding_reference','created_at'),
    )
    id: Mapped[str] = mapped_column(String(36),primary_key=True)
    extraction_id: Mapped[str] = mapped_column(ForeignKey('receipt_extractions.id',ondelete='RESTRICT'))
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id',ondelete='RESTRICT'))
    request_key: Mapped[str] = mapped_column(String(36))
    action: Mapped[str] = mapped_column(String(24))
    field_name: Mapped[str | None] = mapped_column(String(64))
    finding_reference: Mapped[str] = mapped_column(String(100))
    finding_snapshot: Mapped[dict] = mapped_column(JSON)
    reason: Mapped[str] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now())
