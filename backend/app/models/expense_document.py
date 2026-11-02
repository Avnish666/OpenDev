from datetime import datetime
from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class ExpenseDocument(Base):
    __tablename__ = 'expense_documents'
    __table_args__ = (
        CheckConstraint('file_size_bytes > 0 AND file_size_bytes <= 5242880', name='ck_document_size'),
        CheckConstraint("detected_mime_type IN ('application/pdf','image/png','image/jpeg')", name='ck_document_mime'),
        CheckConstraint("sha256_hash ~ '^[0-9a-f]{64}$'", name='ck_document_sha256'),
        CheckConstraint("publication_status IN ('private','published')", name='ck_document_publication'),
        CheckConstraint("publication_status = 'private' OR (redacted_from_id IS NOT NULL AND approved_by IS NOT NULL AND approved_at IS NOT NULL)", name='ck_document_public_approval'),
        CheckConstraint('redacted_from_id IS NULL OR redacted_from_id <> id', name='ck_document_not_self_redacted'),
        Index('ix_documents_expense_hash', 'expense_id', 'sha256_hash'),
        Index('ix_documents_expense_publication', 'expense_id', 'publication_status'),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    expense_id: Mapped[int] = mapped_column(ForeignKey('expenses.id', ondelete='RESTRICT'))
    uploaded_by: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='RESTRICT'), index=True)
    storage_key: Mapped[str] = mapped_column(String(200), unique=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    detected_mime_type: Mapped[str] = mapped_column(String(64))
    file_size_bytes: Mapped[int] = mapped_column(BigInteger)
    sha256_hash: Mapped[str] = mapped_column(String(64))
    publication_status: Mapped[str] = mapped_column(String(24), server_default=text("'private'"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    redacted_from_id: Mapped[str | None] = mapped_column(ForeignKey('expense_documents.id', ondelete='RESTRICT'))
    approved_by: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='RESTRICT'))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
