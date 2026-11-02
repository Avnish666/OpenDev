from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class ReceiptExtraction(Base):
    __tablename__ = 'receipt_extractions'
    __table_args__ = (
        UniqueConstraint('expense_document_id','extraction_version',name='uq_extraction_document_version'),
        CheckConstraint("extraction_status IN ('pending','processing','completed','failed')",name='ck_extraction_status'),
        Index('ix_extraction_document_status','expense_document_id','extraction_status'),
    )
    id: Mapped[str] = mapped_column(String(36),primary_key=True)
    expense_document_id: Mapped[str] = mapped_column(ForeignKey('expense_documents.id',ondelete='RESTRICT'))
    extraction_status: Mapped[str] = mapped_column(String(24))
    extraction_version: Mapped[str] = mapped_column(String(64))
    extracted_json: Mapped[dict | None] = mapped_column(JSON,nullable=True)
    findings_json: Mapped[list | None] = mapped_column(JSON,nullable=True)
    reported_expense_json: Mapped[dict | None] = mapped_column(JSON,nullable=True)
    processing_error_code: Mapped[str | None] = mapped_column(String(64))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now())


class ExtractionAttempt(Base):
    __tablename__ = 'receipt_extraction_attempts'
    __table_args__ = (CheckConstraint("status IN ('processing','completed','failed')",name='ck_extraction_attempt_status'),)
    id: Mapped[str] = mapped_column(String(36),primary_key=True)
    extraction_id: Mapped[str] = mapped_column(ForeignKey('receipt_extractions.id',ondelete='RESTRICT'),index=True)
    triggered_by: Mapped[int] = mapped_column(ForeignKey('users.id',ondelete='RESTRICT'))
    status: Mapped[str] = mapped_column(String(24))
    processing_error_code: Mapped[str | None] = mapped_column(String(64))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
