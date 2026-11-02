from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_optional_user
from app.core.database import get_db
from app.models.expense import Expense
from app.models.user import User
from app.routers.auth import require_trusted_origin
from app.schemas.expense import ExpenseCreate, ExpensePatch, ExpenseResponse, FinancialSummary
from app.services import expenses
from app.services.project_management import can_manage

RecordID = Annotated[int, Path(gt=0, le=9223372036854775807)]

router = APIRouter(prefix='/api', tags=['Reported expenses'])


@router.post('/projects/{project_id}/expenses', response_model=ExpenseResponse, status_code=201, dependencies=[Depends(require_trusted_origin)])
def create_expense(project_id: RecordID, data: ExpenseCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return expenses.create(db, project_id, user, data)


@router.get('/projects/{project_id}/expenses', response_model=list[ExpenseResponse])
def list_expenses(project_id: RecordID, include_drafts: bool = False, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    project = expenses.project_for_expenses(db, project_id, user)
    if include_drafts and not can_manage(db, project, user):
        raise HTTPException(403, 'Draft access requires project owner or maintainer')
    stmt = select(Expense).where(Expense.project_id == project_id)
    if not include_drafts:
        stmt = stmt.where(Expense.publication_status == 'published')
    return db.scalars(stmt.order_by(Expense.expense_date.desc(), Expense.id.desc()).limit(limit).offset(offset)).all()


@router.get('/expenses/{expense_id}', response_model=ExpenseResponse)
def expense_detail(expense_id: RecordID, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    return expenses.get(db, expense_id, user)


@router.patch('/expenses/{expense_id}', response_model=ExpenseResponse, dependencies=[Depends(require_trusted_origin)])
def edit_expense(expense_id: RecordID, data: ExpensePatch, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return expenses.edit(db, expense_id, user, data)


@router.post('/expenses/{expense_id}/publish', response_model=ExpenseResponse, dependencies=[Depends(require_trusted_origin)])
def publish_expense(expense_id: RecordID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return expenses.publish(db, expense_id, user)


@router.get('/projects/{project_id}/financial-summary', response_model=FinancialSummary)
def financial_summary(project_id: RecordID, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    project = expenses.project_for_expenses(db, project_id, user)
    return expenses.summary(db, project)
