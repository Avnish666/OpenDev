from datetime import datetime, timezone, timedelta
import hashlib
from pathlib import Path
import tempfile
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from app.models.expense import Expense
from app.models.expense_document import ExpenseDocument
from app.models.receipt_extraction import ReceiptExtraction, ExtractionAttempt
from app.schemas.extraction import ExtractedReceipt
from app.services import documents
from app.services.storage import download_private
from app.services.receipt import provider as providers
from app.services.receipt.findings import detect, snapshot

VERSION=providers.EXTRACTION_VERSION
SLOT_KEY=72333003
LEASE_SECONDS=180


def managed_document(db,document_id,user):
    doc,_=documents.accessible(db,document_id,user)
    documents.authorize_upload(db,doc.expense_id,user)
    return doc


def current(db,document_id):
    return db.scalar(select(ReceiptExtraction).where(ReceiptExtraction.expense_document_id==document_id,ReceiptExtraction.extraction_version==VERSION).execution_options(populate_existing=True))


def view(db,record,expense):
    receipt=ExtractedReceipt.model_validate(record.extracted_json) if record.extracted_json else None
    doc=db.get(ExpenseDocument,record.expense_document_id)
    reported=snapshot(expense)
    return dict(id=record.id,expense_document_id=record.expense_document_id,extraction_status=record.extraction_status,extraction_version=record.extraction_version,
                extracted_json=receipt,findings_json=detect(db,doc,expense,receipt) if receipt else [],reported_expense=reported,
                comparison_is_stale=record.reported_expense_json is not None and record.reported_expense_json!=reported,
                processing_error_code=record.processing_error_code,started_at=record.started_at,completed_at=record.completed_at,created_at=record.created_at,
                attempts=db.scalars(select(ExtractionAttempt).where(ExtractionAttempt.extraction_id==record.id).order_by(ExtractionAttempt.started_at)).all())


def process(db,doc,user,retry=False):
    # Persist a unique pending record before expensive work. Duplicate POSTs reuse it.
    db.execute(insert(ReceiptExtraction).values(id=str(uuid4()),expense_document_id=doc.id,extraction_version=VERSION,extraction_status='pending').on_conflict_do_nothing(index_elements=['expense_document_id','extraction_version']))
    db.commit()
    record=current(db,doc.id)
    if record.extraction_status=='completed' or (record.extraction_status=='failed' and not retry): return record
    # A dedicated connection owns the transaction advisory lock; commits cannot return it
    # to the pool while still locked. One worker across instances using this DB.
    with db.get_bind().engine.connect() as slot:
        acquired=slot.scalar(select(func.pg_try_advisory_xact_lock(SLOT_KEY)))
        if not acquired: return record
        try:
            record=db.scalar(select(ReceiptExtraction).where(ReceiptExtraction.id==record.id).with_for_update().execution_options(populate_existing=True))
            now=datetime.now(timezone.utc)
            if record.extraction_status=='completed': return record
            if record.extraction_status=='processing' and record.started_at and now-record.started_at.replace(tzinfo=timezone.utc)<timedelta(seconds=LEASE_SECONDS):return record
            if record.extraction_status=='failed' and not retry:return record
            for old in db.scalars(select(ExtractionAttempt).where(ExtractionAttempt.extraction_id==record.id,ExtractionAttempt.status=='processing')):
                old.status='failed';old.processing_error_code='WORKER_RESTARTED';old.completed_at=now
            record.extraction_status='processing';record.started_at=now;record.completed_at=None;record.processing_error_code=None
            attempt=ExtractionAttempt(id=str(uuid4()),extraction_id=record.id,triggered_by=user.id,status='processing',started_at=now)
            db.add(attempt);db.commit()
            result=None;error=None
            try:
                with tempfile.TemporaryDirectory(prefix='opendev-extract-') as folder:
                    path=Path(folder)/'receipt'
                    size=download_private(documents.storage,doc.storage_key,path,documents.MAX_BYTES)
                    if size!=doc.file_size_bytes or hashlib.sha256(path.read_bytes()).hexdigest()!=doc.sha256_hash:
                        raise providers.ExtractionError('DOCUMENT_INTEGRITY')
                    if documents.validate(path)!=doc.detected_mime_type:
                        raise providers.ExtractionError('DOCUMENT_TYPE')
                    result=providers.provider.extract(path,doc.detected_mime_type)
                    result=ExtractedReceipt.model_validate(result)
            except providers.ExtractionError as exc:error=exc.code
            except HTTPException as exc:error='DOCUMENT_TOO_LARGE' if exc.status_code==413 else 'INVALID_DOCUMENT' if exc.status_code==415 else 'STORAGE_DOWNLOAD_FAILED'
            except Exception:error='PROCESSING_FAILED'
            # Receipt fields never modify Expense or Contribution. Findings are a separate snapshot.
            expense=db.get(Expense,doc.expense_id,populate_existing=True)
            record.extraction_status=attempt.status='failed' if error else 'completed'
            record.processing_error_code=attempt.processing_error_code=error
            record.completed_at=attempt.completed_at=datetime.now(timezone.utc)
            if result and not error:
                record.extracted_json=result.model_dump(mode='json');record.reported_expense_json=snapshot(expense)
                record.findings_json=detect(db,doc,expense,result)
            db.commit()
            return record
        finally:
            slot.rollback()
