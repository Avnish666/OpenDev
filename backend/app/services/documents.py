import json
import logging
import subprocess
import sys
import os
import signal
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.models.expense_document import ExpenseDocument
from app.models.project import Project
from app.models.user import User
from app.services import expenses
from app.services.project_management import can_manage
from app.services.storage import storage, UploadFailure
from app.services.decoder_limits import decoder_slot

MAX_BYTES = 5 * 1024 * 1024
logger = logging.getLogger(__name__)


def authorize_upload(db, expense_id, user):
    expense = expenses.get(db, expense_id, user)
    project = db.get(Project, expense.project_id)
    if not can_manage(db, project, user):
        raise HTTPException(403, 'Project owner or maintainer required')


_validation_slot=decoder_slot

def validate(path):
    if not _validation_slot.acquire(blocking=False):
        raise HTTPException(429,'Document validator busy; retry later',headers={'Retry-After':'5'})
    try:return _validate(path)
    finally:_validation_slot.release()


def _validate(path):
    worker = Path(__file__).with_name('document_validation_worker.py')
    try:
        with tempfile.TemporaryFile() as output:
            process = subprocess.Popen([sys.executable, '-I', str(worker), str(path)],
                env={}, stdout=output, stderr=subprocess.DEVNULL, start_new_session=True)
            try:
                process.communicate(timeout=8)
            except subprocess.TimeoutExpired:
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                process.communicate()
                raise ValueError() from None
            if process.returncode or os.fstat(output.fileno()).st_size>4096:
                raise ValueError()
            output.seek(0)
            mime = json.loads(output.read(4097))['mime']
        if mime not in ('application/pdf', 'image/png', 'image/jpeg'):
            raise ValueError()
        return mime
    except (subprocess.SubprocessError, ValueError, KeyError):
        raise HTTPException(415, 'Invalid or unsafe PDF, PNG or JPEG content') from None


def filename(value):
    name = unquote(value).replace('\\', '/').rsplit('/', 1)[-1].strip()
    if not name or len(name) > 255 or any(ord(c) < 32 or ord(c) == 127 for c in name):
        raise HTTPException(422, 'Invalid original filename')
    return name


def cleanup(key, document_id):
    try:
        storage.delete(key)
    except Exception:
        # Correlation ID only: never log keys, filenames, URLs, content or credentials.
        logger.error('Receipt cleanup needs reconciliation for document %s', document_id)
        raise HTTPException(503, f'Upload failed; storage cleanup needs reconciliation (document {document_id})') from None


def upload(db, expense_id, user, path, original_filename, size, digest, source_id=None):
    from app.core.features import require_receipts
    require_receipts()
    mime = validate(path)
    expense = expenses.get(db, expense_id, user, write=True)
    if size <= 0 or size > MAX_BYTES:
        raise HTTPException(413, 'File must contain 1 to 5242880 bytes')
    source = db.get(ExpenseDocument, source_id) if source_id else None
    if source_id and (not source or source.expense_id != expense.id):
        raise HTTPException(404, 'Original document not found for this expense')
    if source and source.sha256_hash == digest:
        raise HTTPException(422, 'A redacted version must differ from its original')
    doc_id = str(uuid4())
    key = f'receipts/{uuid4()}'
    doc = ExpenseDocument(id=doc_id, expense_id=expense.id, uploaded_by=user.id, storage_key=key,
                          original_filename=original_filename, detected_mime_type=mime, file_size_bytes=size,
                          sha256_hash=digest, publication_status='private', redacted_from_id=source_id)
    try:
        storage.upload(key, path, mime)
    except UploadFailure as error:
        db.rollback()
        if error.cleanup_safe:
            cleanup(key, doc_id)
        raise
    try:
        db.add(doc)
        db.flush()
        # Construct the safe response before commit: no post-commit serialization work can trigger cleanup.
        result = view(db, doc, manager=True)
        db.commit()
        return result
    except Exception:
        db.rollback()
        # A disconnected COMMIT can be ambiguous. Never delete an object with committed metadata.
        try:
            exists = db.get(ExpenseDocument, doc_id) is not None
        except Exception:
            logger.error('Receipt commit outcome needs reconciliation for document %s', doc_id)
            raise HTTPException(503, f'Upload outcome needs reconciliation (document {doc_id})') from None
        if not exists:
            cleanup(key, doc_id)
        raise HTTPException(503, 'Document metadata could not be saved') from None


def is_public(doc, expense, project):
    return (project.status in ('active','paused','completed') and expense.publication_status == 'published' and
            doc.publication_status == 'published' and doc.redacted_from_id is not None and
            doc.approved_by is not None and doc.approved_at is not None)


def accessible(db, document_id, user=None):
    doc = db.get(ExpenseDocument, document_id)
    if doc is None:
        raise HTTPException(404, 'Document not found')
    expense = db.get(Expense, doc.expense_id)
    project = db.get(Project, expense.project_id)
    manager = can_manage(db, project, user)
    if not manager and not is_public(doc, expense, project):
        raise HTTPException(404, 'Document not found')
    return doc, manager


def view(db, doc, manager):
    duplicate = None
    if manager:
        project_id = db.scalar(select(Expense.project_id).where(Expense.id == doc.expense_id))
        duplicate = db.scalar(select(func.count()).select_from(ExpenseDocument).join(Expense).where(
            Expense.project_id == project_id, ExpenseDocument.sha256_hash == doc.sha256_hash, ExpenseDocument.id != doc.id)) > 0
    return dict(id=doc.id, expense_id=doc.expense_id, original_filename=doc.original_filename,
                detected_mime_type=doc.detected_mime_type, file_size_bytes=doc.file_size_bytes,
                publication_status=doc.publication_status, created_at=doc.created_at,
                is_redacted_version=doc.redacted_from_id is not None, duplicate_in_project=duplicate)


def publish(db, document_id, user, approved):
    doc = db.get(ExpenseDocument, document_id)
    if not doc:
        raise HTTPException(404, 'Document not found')
    expense = expenses.get(db, doc.expense_id, user, write=True)
    doc = db.scalar(select(ExpenseDocument).where(ExpenseDocument.id == document_id).with_for_update().execution_options(populate_existing=True))
    if approved:
        if not doc.redacted_from_id:
            raise HTTPException(409, 'Original receipts cannot be published; upload a separate redacted version')
        if expense.publication_status != 'published' or db.get(Project, expense.project_id).status == 'draft':
            raise HTTPException(409, 'Publish the project and expense before approving redacted evidence')
        source = db.get(ExpenseDocument, doc.redacted_from_id)
        if source.expense_id != expense.id or source.sha256_hash == doc.sha256_hash:
            raise HTTPException(409, 'Invalid redacted evidence relationship')
        doc.publication_status = 'published'
        doc.approved_by = user.id
        doc.approved_at = datetime.now(timezone.utc)
    else:
        doc.publication_status = 'private'
        doc.approved_by = None
        doc.approved_at = None
    expenses.commit(db)
    return view(db, doc, manager=True)
