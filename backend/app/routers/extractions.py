from uuid import UUID
from fastapi import APIRouter, Body, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.expense import Expense
from app.models.expense_document import ExpenseDocument
from app.models.receipt_extraction import ReceiptExtraction
from app.routers.auth import require_trusted_origin
from app.routers.expenses import RecordID
from app.schemas.extraction import ExtractionResponse, TriggerExtraction
from app.services import expenses
from app.services.receipt import pipeline

router=APIRouter(prefix='/api',tags=['Private receipt intelligence'])


def no_cache(response):
    response.headers['Cache-Control']='no-store'
    response.headers['Referrer-Policy']='no-referrer'


@router.post('/documents/{document_id}/extract',response_model=ExtractionResponse,dependencies=[Depends(require_trusted_origin)])
def extract_document(document_id: UUID,response: Response,data: TriggerExtraction=Body(default_factory=TriggerExtraction),db: Session=Depends(get_db),user: User=Depends(get_current_user)):
    no_cache(response)
    doc=pipeline.managed_document(db,str(document_id),user)
    if doc.redacted_from_id:
        raise HTTPException(409,'Extract the private original, not a redacted publication copy')
    record=pipeline.process(db,doc,user,retry=data.retry)
    # Membership is checked again after processing before private results are returned.
    pipeline.managed_document(db,str(document_id),user)
    response.status_code=202 if record.extraction_status in ('pending','processing') else 200
    return pipeline.view(db,record,db.get(Expense,doc.expense_id,populate_existing=True))


@router.get('/documents/{document_id}/extraction',response_model=ExtractionResponse)
def get_extraction(document_id: UUID,response: Response,db: Session=Depends(get_db),user: User=Depends(get_current_user)):
    no_cache(response)
    doc=pipeline.managed_document(db,str(document_id),user)
    record=pipeline.current(db,doc.id)
    if not record:raise HTTPException(404,'No extraction exists for the current extractor version')
    return pipeline.view(db,record,db.get(Expense,doc.expense_id))


@router.get('/expenses/{expense_id}/discrepancies',response_model=list[ExtractionResponse])
def discrepancies(expense_id: RecordID,response: Response,db: Session=Depends(get_db),user: User=Depends(get_current_user)):
    no_cache(response)
    documents_expense=expenses.get(db,expense_id,user,write=True)
    records=db.scalars(select(ReceiptExtraction).join(ExpenseDocument).where(ExpenseDocument.expense_id==expense_id,ReceiptExtraction.extraction_version==pipeline.VERSION).order_by(ReceiptExtraction.created_at.desc())).all()
    return [pipeline.view(db,record,documents_expense) for record in records]
