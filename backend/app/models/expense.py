"""Maintainer-reported expenses; publication is not payment verification."""
from datetime import date, datetime

from sqlalchemy import BigInteger, CheckConstraint, Date, DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Expense(Base):
    __tablename__ = 'expenses'
    __table_args__ = (
        CheckConstraint('amount_cents > 0', name='ck_expense_positive_amount'),
        CheckConstraint("currency = 'USD'", name='ck_expense_currency'),
        CheckConstraint("length(trim(category)) > 0", name='ck_expense_category'),
        CheckConstraint("length(trim(vendor)) > 0", name='ck_expense_vendor'),
        CheckConstraint("length(trim(description)) > 0", name='ck_expense_description'),
        CheckConstraint("evidence_status = 'unverified'", name='ck_expense_evidence_status'),
        CheckConstraint("publication_status IN ('draft', 'published')", name='ck_expense_publication_status'),
        Index('ix_expenses_project_publication_date', 'project_id', 'publication_status', 'expense_date', 'id'),
        Index('ix_expenses_project_category', 'project_id', 'category'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id', ondelete='RESTRICT'), nullable=False)
    submitted_by_user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='RESTRICT'), index=True)
    category: Mapped[str] = mapped_column(String(100))
    amount_cents: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3))
    vendor: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    expense_date: Mapped[date] = mapped_column(Date)
    evidence_status: Mapped[str] = mapped_column(String(24), server_default=text("'unverified'"))
    publication_status: Mapped[str] = mapped_column(String(24), server_default=text("'draft'"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
