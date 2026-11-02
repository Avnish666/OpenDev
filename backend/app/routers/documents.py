import asyncio
import hashlib
import tempfile
from pathlib import Path as FilePath
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.auth import get_current_user, get_optional_user
from app.core.database import get_db
from app.models.expense_document import ExpenseDocument
from app.models.project import Project
from app.models.user import User
from app.routers.auth import require_trusted_origin
from app.routers.expenses import RecordID
from app.schemas.document import DocumentResponse, DownloadResponse, PublishDocument
from app.services import documents, expenses
from app.services.project_management import can_manage

router = APIRouter(prefix='/api', tags=['Private expense evidence'])


def no_cache(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Referrer-Policy'] = 'no-referrer'


@router.post('/expenses/{expense_id}/documents', response_model=DocumentResponse, status_code=201,
             dependencies=[Depends(require_trusted_origin)],
             openapi_extra={'requestBody': {'required': True, 'content': {mime: {'schema': {'type': 'string', 'format': 'binary'}} for mime in ['application/pdf', 'image/png', 'image/jpeg']}}})
async def upload_document(expense_id: RecordID, request: Request, response: Response,
                          x_filename: str = Header(max_length=2048), redacted_from_id: UUID | None = None,
                          db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    no_cache(response)
    # Authenticate and authorize before consuming any upload data or contacting storage.
    await run_in_threadpool(documents.authorize_upload, db, expense_id, user)
    name = documents.filename(x_filename)
    length = request.headers.get('content-length')
    if length:
        try:
            if int(length) < 0 or int(length) > documents.MAX_BYTES:
                raise HTTPException(413, 'Maximum upload size is 5 MiB')
        except ValueError:
            raise HTTPException(400, 'Invalid Content-Length') from None
    digest = hashlib.sha256(); size = 0
    with tempfile.NamedTemporaryFile(prefix='opendev-receipt-', delete=False) as target:
        path = FilePath(target.name)
        try:
            async with asyncio.timeout(20):
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > documents.MAX_BYTES:
                        raise HTTPException(413, 'Maximum upload size is 5 MiB')
                    # Bounded by total size; no multipart parser buffers an unbounded request.
                    target.write(chunk); digest.update(chunk)
            target.flush()
            if not size:
                raise HTTPException(422, 'File must not be empty')
            return await run_in_threadpool(documents.upload, db, expense_id, user, path, name, size,
                                          digest.hexdigest(), str(redacted_from_id) if redacted_from_id else None)
        except TimeoutError:
            raise HTTPException(408, 'Upload timed out') from None
        finally:
            path.unlink(missing_ok=True)


@router.get('/expenses/{expense_id}/documents', response_model=list[DocumentResponse])
def list_documents(expense_id: RecordID, response: Response, limit: int = Query(20, ge=1, le=100),
                   offset: int = Query(0, ge=0), db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    no_cache(response)
    expense = expenses.get(db, expense_id, user)
    project = db.get(Project, expense.project_id)
    manager = can_manage(db, project, user)
    stmt = select(ExpenseDocument).where(ExpenseDocument.expense_id == expense.id)
    if not manager:
        stmt = stmt.where(ExpenseDocument.publication_status == 'published', ExpenseDocument.redacted_from_id.is_not(None),
                          ExpenseDocument.approved_by.is_not(None), ExpenseDocument.approved_at.is_not(None))
    docs = db.scalars(stmt.order_by(ExpenseDocument.created_at.desc(), ExpenseDocument.id).limit(limit).offset(offset)).all()
    return [documents.view(db, doc, manager) for doc in docs]


@router.get('/documents/{document_id}/download', response_model=DownloadResponse)
def download_document(document_id: UUID, response: Response, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    no_cache(response)
    doc, _ = documents.accessible(db, str(document_id), user)
    return {'url': documents.storage.signed_url(doc.storage_key, doc.detected_mime_type), 'expires_in': 60}


@router.post('/documents/{document_id}/publish', response_model=DocumentResponse, dependencies=[Depends(require_trusted_origin)])
def publish_document(document_id: UUID, data: PublishDocument, response: Response,
                     db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    no_cache(response)
    return documents.publish(db, str(document_id), user, approved=True)


@router.post('/documents/{document_id}/unpublish', response_model=DocumentResponse, dependencies=[Depends(require_trusted_origin)])
def unpublish_document(document_id: UUID, response: Response, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    no_cache(response)
    return documents.publish(db, str(document_id), user, approved=False)
